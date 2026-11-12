import { expect, test } from "@playwright/test";
import { completeMFA } from "./mfa-helper.js";

async function login(page, username) {
  await page.goto("/app/login");
  await page.getByLabel("Usuario").fill(username);
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  if (username.includes("admin")) await completeMFA(page, username);
}

async function navigateWithinApp(page, path) {
  await page.evaluate((url) => {
    history.pushState({}, "", url);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, path);
}

test("a doctor switches clinics without seeing the other clinic and loses access after suspension", async ({
  page,
  browser,
}) => {
  await login(page, "e2e_tenant_doctor");
  await page.getByRole("button", { name: "Clínica E2E A" }).click();
  await expect(page.getByRole("heading", { name: /Bienvenido/ })).toBeVisible();
  await navigateWithinApp(page, "/app/patients/list");
  await expect(page.getByText("SINTETICOA", { exact: false })).toBeVisible();
  await expect(page.getByText("SINTETICOB", { exact: false })).toHaveCount(0);
  const patientLink = page.getByRole("link", { name: "Ver SINTETICOA" });
  const patientUrl = await patientLink.getAttribute("href");
  expect(patientUrl).toBeTruthy();
  await page
    .getByLabel("Clínica actual")
    .selectOption({ label: "Clínica E2E B" });
  await expect(page.getByRole("heading", { name: /Bienvenido/ })).toBeVisible();
  await navigateWithinApp(page, "/app/patients/list");
  await expect(page.getByText("SINTETICOB", { exact: false })).toBeVisible();
  await expect(page.getByText("SINTETICOA", { exact: false })).toHaveCount(0);
  await navigateWithinApp(page, patientUrl);
  await expect(page.getByText("SINTETICOA", { exact: false })).toHaveCount(0);
  await expect(page.getByRole("alert")).toBeVisible();

  const adminContext = await browser.newContext();
  const admin = await adminContext.newPage();
  try {
    await login(admin, "e2e_tenant_admin");
    await admin.getByRole("button", { name: "Clínica E2E B" }).click();
    const doctorRow = admin
      .getByRole("row")
      .filter({ hasText: "e2e_tenant_doctor" });
    await doctorRow.getByRole("button", { name: "Suspender" }).click();
    await admin
      .getByRole("dialog")
      .getByRole("button", { name: "Confirmar cambio" })
      .click();
    await expect(
      doctorRow.getByRole("button", { name: "Reactivar" }),
    ).toBeVisible();
    await navigateWithinApp(page, "/app/patients/list");
    await expect(page.getByText("SINTETICOB", { exact: false })).toHaveCount(0);
    await expect(page.getByRole("alert")).toBeVisible();
    await doctorRow.getByRole("button", { name: "Revocar" }).click();
    await admin
      .getByRole("dialog")
      .getByRole("button", { name: "Confirmar cambio" })
      .click();
    await expect(doctorRow).toContainText("Requiere una nueva invitación");
  } finally {
    await adminContext.close();
  }
});

test("platform administrator onboards and activates a synthetic clinic", async ({
  page,
}) => {
  await login(page, "e2e_platform_admin");
  await page.getByRole("link", { name: "Administración", exact: true }).click();
  await page.getByRole("link", { name: "Clínicas", exact: true }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Clínica E2E Nueva");
  await page.getByLabel("Identificador").fill("clinica-e2e-nueva");
  await page
    .getByLabel("Correo del administrador inicial")
    .fill("synthetic-admin@example.test");
  await page.getByRole("button", { name: "Crear y enviar invitación" }).click();
  const clinicRow = page
    .getByRole("row")
    .filter({ hasText: "Clínica E2E Nueva" });
  await expect(clinicRow).toContainText("Inactiva");
  await clinicRow.getByRole("button", { name: "Activar", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar cambio" })
    .click();
  await expect(clinicRow.locator('td[data-label="Estado"]')).toContainText(
    "Activa",
  );
  await expect(clinicRow.locator('td[data-label="IA"]')).toContainText(
    "Desactivada",
  );
  await clinicRow
    .getByRole("button", { name: "Activar IA", exact: true })
    .click();
  await expect(clinicRow.locator('td[data-label="IA"]')).toContainText(
    "Activa",
  );
  await clinicRow
    .getByRole("button", { name: "Desactivar IA", exact: true })
    .click();
  await expect(clinicRow.locator('td[data-label="IA"]')).toContainText(
    "Desactivada",
  );
  await expect(clinicRow.locator('td[data-label="Estado"]')).toContainText(
    "Activa",
  );
  await clinicRow
    .getByRole("button", { name: "Administración inicial" })
    .click();
  await expect(page.getByText("synthetic-admin@example.test")).toBeVisible();
});

test("core multitenant covers records, private files, exports and reception without cross-clinic access", async ({
  page,
  request,
}) => {
  test.setTimeout(120000);
  const { Buffer } = await import("node:buffer");
  const image = {
    name: "synthetic.png",
    mimeType: "image/png",
    buffer: Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
      "base64",
    ),
  };
  const auth = await request.post("/api/v1/auth/login/", {
    data: { username: "e2e_tenant_doctor", password: "e2e_password_123" },
  });
  expect(auth.status()).toBe(200);
  const token = (await auth.json()).access;
  const clinics = await (
    await request.get("/api/v1/clinics/memberships/", {
      headers: { Authorization: `Bearer ${token}` },
    })
  ).json();
  const a = clinics.find((c) => c.slug === "e2e-tenant-a");
  const headers = { Authorization: `Bearer ${token}`, "X-Clinic-ID": a.id };
  // B was revoked by the preceding scenario, so a forged B header must fail.
  const deniedHeaders = {
    ...headers,
    "X-Clinic-ID": "11111111-1111-4111-8111-111111111111",
  };
  const id = String(Date.now()).slice(-8);
  const created = await request.post("/api/v1/clinics/patients/", {
    headers,
    data: {
      nombre: `CIERRE${id}`,
      appat: "PRUEBA",
      apmat: "DEMO",
      fecha_nacimiento: "1990-01-01",
      genero: "F",
      telefono: `55${id}`,
      email: `closure-${id}@example.test`,
    },
  });
  expect(created.status()).toBe(201);
  const patient = (await created.json()).id;
  const base = `/api/v1/clinics/patients/${patient}/`;
  expect(
    (
      await request.put(base + "medical-history/", {
        headers,
        data: { version: 0, otros: "Sintético" },
      })
    ).status(),
  ).toBe(200);
  expect(
    (
      await request.put(base + "odontogram/", {
        headers,
        data: {
          version: 0,
          denticion_permanente: {},
          denticion_decidua: {},
          resumen: {},
        },
      })
    ).status(),
  ).toBe(200);
  const consultation = await request.post(base + "consultations/", {
    headers,
    data: { motivo_consulta: "Control sintético" },
  });
  expect(consultation.status()).toBe(201);
  const consultationId = (await consultation.json()).id;
  const upload = await request.post(base + "clinical-images/", {
    headers,
    multipart: {
      imagen: image,
      consulta_id: String(consultationId),
      tipo_imagen: "RX",
      descripcion: "Imagen sintética de cierre",
    },
  });
  expect(upload.status(), await upload.text()).toBe(201);
  const imageId = (await upload.json()).id;
  const analyze = await request.post(
    `/api/v1/clinics/clinical-images/${imageId}/analyze/`,
    { headers, data: {} },
  );
  expect(analyze.status()).toBe(200);
  const run = (await analyze.json()).run_id;
  expect(
    (
      await request.get(
        `/api/v1/clinics/clinical-images/${imageId}/analysis-runs/${run}/file/`,
        { headers },
      )
    ).status(),
  ).toBe(200);
  const templates = (
    await (await request.get(base + "consent/", { headers })).json()
  ).templates;
  const signedPDF = {
    name: "signed-synthetic.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\nsynthetic\n%%EOF"),
  };
  const consent = await request.post(base + "consent/", {
    headers,
    multipart: {
      template_id: String(templates[0].id),
      signer_name: "Paciente Sintético",
      signer_role: "PATIENT",
      signed_on: "2026-01-01",
      attested: "true",
      signed_document: signedPDF,
    },
  });
  expect(consent.status()).toBe(201);
  const evidenceId = (await consent.json()).id;
  const pdf = await request.get(base + `consent/records/${evidenceId}/file/`, {
    headers,
  });
  expect(pdf.status()).toBe(423);
  expect((await pdf.json()).detail).toContain("cuarentena");
  const fields = [
    "antes_oclusal_superior",
    "antes_lateral_izquierda",
    "antes_frontal",
    "antes_lateral_derecha",
    "antes_oclusal_inferior",
  ];
  const study = await request.put(base + "comparative-study/", {
    headers,
    multipart: {
      fecha_inicio: "2030-01-15",
      diagnostico: "Prueba",
      ...Object.fromEntries(fields.map((field) => [field, image])),
    },
  });
  expect(study.status()).toBe(200);
  expect(
    (await request.get(base + "comparative-study/pdf/", { headers })).status(),
  ).toBe(200);
  for (const kind of ["patients", "consultations", "clinical-images"]) {
    expect(
      (
        await request.get(`/api/v1/clinics/exports/${kind}.xlsx`, { headers })
      ).status(),
    ).toBe(200);
  }
  expect(
    (
      await request.post(base + "email/", {
        headers,
        data: { asunto: "Control", mensaje: "Prueba" },
      })
    ).status(),
  ).toBe(200);
  for (const path of [
    base,
    base + "medical-history/",
    base + "consent/identity/file/",
    base + "consent/pdf/file/",
    base + "comparative-study/pdf/",
    `/api/v1/clinics/clinical-images/${imageId}/original/file/`,
  ]) {
    expect((await request.get(path, { headers: deniedHeaders })).status()).toBe(
      403,
    );
  }
  expect(
    (await request.get("/api/v1/patients.json", { headers })).status(),
  ).toBe(410);
  await login(page, "e2e_tenant_staff");
  await page.getByRole("button", { name: "Clínica E2E A" }).click();
  await expect(
    page.getByRole("heading", { name: "Agenda de recepción" }),
  ).toBeVisible();
  await page.getByLabel("Buscar paciente").fill(`CIERRE${id}`);
  await expect(
    page.getByRole("option", { name: new RegExp(`CIERRE${id}`) }),
  ).toHaveCount(1);
  await page
    .getByRole("combobox", { name: "Paciente", exact: true })
    .selectOption(String(patient), { timeout: 5000 });
  await page.getByLabel("Fecha", { exact: true }).fill("2099-01-01");
  await page.getByLabel("Motivo de la cita").fill("Recepción sintética");
  await page.getByRole("button", { name: "Guardar cita" }).click();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Cita guardada correctamente." }),
  ).toBeVisible();
  const row = page.getByRole("row").filter({ hasText: `CIERRE${id}` });
  await row.getByRole("button", { name: "Anular" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar cambio" })
    .click();
  await expect(row).toContainText("Anulada");
  await page
    .getByLabel("Clínica actual")
    .selectOption({ label: "Clínica E2E B" });
  await expect(page.getByText(`CIERRE${id}`, { exact: false })).toHaveCount(0);
});
