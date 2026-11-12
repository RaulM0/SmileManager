import { expect, test } from "@playwright/test";
import { createHmac } from "node:crypto";
import { Buffer } from "node:buffer";
import { completeMFA } from "./mfa-helper.js";

function codeFor(secret) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const bits = [...secret.replace(/=+$/, "")]
    .map((char) => alphabet.indexOf(char).toString(2).padStart(5, "0"))
    .join("");
  const bytes = Buffer.from(
    bits.match(/.{8}/g).map((byte) => parseInt(byte, 2)),
  );
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const hash = createHmac("sha1", bytes).update(counter).digest();
  const offset = hash[hash.length - 1] & 15;
  return String((hash.readUInt32BE(offset) & 0x7fffffff) % 1000000).padStart(
    6,
    "0",
  );
}

test("MFA enrollment, recovery and immediate revocation of another session", async ({
  page,
  request,
}) => {
  const username = "e2e_new_mfa_admin";
  await page.goto("login");
  await page.getByLabel("Usuario", { exact: true }).fill(username);
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page
    .getByRole("button", { name: "Iniciar sesión", exact: true })
    .click();
  const secret = await page.getByLabel("Clave del autenticador").textContent();
  await page
    .getByLabel("Código del autenticador o de recuperación")
    .fill(codeFor(secret));
  await page.getByRole("button", { name: "Verificar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Guarda tus códigos de recuperación" }),
  ).toBeVisible();
  const codes = await page
    .getByRole("region", { name: "Códigos de recuperación" })
    .locator("li code")
    .allTextContents();
  expect(codes).toHaveLength(10);
  await page.getByRole("button", { name: "He guardado los códigos" }).click();
  await page.goto("/app/security");
  await expect(page.getByText("Segundo factor: Configurado.")).toBeVisible();
  const challenge = await (
    await request.post("/api/v1/auth/login/", {
      data: { username, password: "e2e_password_123" },
    })
  ).json();
  expect(challenge.access).toBeUndefined();
  const other = await (
    await request.post("/api/v1/auth/mfa/verify/", {
      data: { challenge: challenge.challenge, code: codes[0] },
    })
  ).json();
  expect(other.access).toBeTruthy();
  const headers = { Authorization: `Bearer ${other.access}` };
  expect(
    (await request.get("/api/v1/auth/sessions/", { headers })).status(),
  ).toBe(200);
  await page.getByRole("button", { name: "Cerrar las otras sesiones" }).click();
  await expect
    .poll(async () =>
      (await request.get("/api/v1/auth/sessions/", { headers })).status(),
    )
    .toBe(401);
  const again = await (
    await request.post("/api/v1/auth/login/", {
      data: { username, password: "e2e_password_123" },
    })
  ).json();
  expect(
    (
      await request.post("/api/v1/auth/mfa/verify/", {
        data: { challenge: again.challenge, code: codes[0] },
      })
    ).status(),
  ).toBe(401);
});

test("clinic publishes a versioned notice that is available without login", async ({
  page,
  browser,
}) => {
  await page.goto("login");
  await page.getByLabel("Usuario", { exact: true }).fill("e2e_tenant_admin");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page
    .getByRole("button", { name: "Iniciar sesión", exact: true })
    .click();
  await completeMFA(page, "e2e_tenant_admin");
  await page
    .getByRole("button", { name: "Clínica E2E A", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Configurar privacidad y consentimientos" })
    .click();
  await page
    .getByLabel("Nombre legal o razón social del responsable")
    .fill("Responsable Sintético Etapa 2");
  await page
    .getByLabel(
      "El responsable revisó estos datos y los procedimientos están disponibles para los titulares.",
    )
    .check();
  await page
    .getByRole("button", { name: "Publicar nueva versión del aviso" })
    .click();
  await expect(page.getByText("Aviso versión 2 publicado.")).toBeVisible();
  const context = await browser.newContext();
  try {
    const publicPage = await context.newPage();
    await publicPage.goto("http://127.0.0.1:8010/app/privacy/e2e-tenant-a");
    await expect(
      publicPage.getByText("Responsable Sintético Etapa 2"),
    ).toBeVisible();
    await expect(publicPage.getByText(/Versión 2/)).toBeVisible();
  } finally {
    await context.close();
  }
});
