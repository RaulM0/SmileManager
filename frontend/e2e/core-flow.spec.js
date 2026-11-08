import { expect, test } from "@playwright/test";
import { Buffer } from "node:buffer";

const tinyImage = {
  name: "clinical.png",
  mimeType: "image/png",
  buffer: Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
    "base64",
  ),
};

async function expectResponsiveWidths(page) {
  for (const width of [320, 360, 390, 768]) {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 1024 });
    await expect
      .poll(async () => (await page.locator(".workspace-sidebar").boundingBox()).x)
      .toBeLessThan(-200);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBeLessThanOrEqual(width);
  }
  await page.setViewportSize({ width: 1280, height: 720 });
}

async function captureFormVariants(page, name) {
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 800 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: `.e2e-closure-artifacts/${name}-${width}.png`, fullPage: true });
  }
  await page.setViewportSize({ width: 1280, height: 720 });
}

async function expectTabSequence(page, locators) {
  for (let index = 0; index < locators.length - 1; index += 1) {
    await locators[index].press("Tab");
    await expect(locators[index + 1]).toBeFocused();
  }
}

async function expectRoutesAtAllWidths(page, paths, capturePaths = []) {
  for (const path of paths) {
    await page.goto(path);
    await expect(page.locator("#main-content h1").first(), path).toBeVisible();
    const unnamedButtons = await page.locator("#main-content button").evaluateAll((buttons) => buttons
      .filter((button) => button.getClientRects().length > 0)
      .filter((button) => !button.getAttribute("aria-label") && !button.getAttribute("aria-labelledby") && !button.getAttribute("title") && !button.textContent.trim())
      .map((button) => button.outerHTML.slice(0, 160)));
    expect(unnamedButtons, `Botones sin nombre accesible en ${path}`).toEqual([]);
    const unnamedFields = await page.locator("#main-content input, #main-content select, #main-content textarea").evaluateAll((fields) => fields
      .filter((field) => field.getClientRects().length > 0 && field.type !== "hidden")
      .filter((field) => !field.labels?.length && !field.getAttribute("aria-label") && !field.getAttribute("aria-labelledby"))
      .map((field) => field.outerHTML.slice(0, 160)));
    expect(unnamedFields, `Campos sin etiqueta en ${path}`).toEqual([]);
    const unnamedLinks = await page.locator("#main-content a").evaluateAll((links) => links
      .filter((link) => link.getClientRects().length > 0)
      .filter((link) => !link.getAttribute("aria-label") && !link.getAttribute("aria-labelledby") && !link.textContent.trim() && !link.querySelector("img[alt]:not([alt=''])"))
      .map((link) => link.outerHTML.slice(0, 160)));
    expect(unnamedLinks, `Enlaces sin nombre accesible en ${path}`).toEqual([]);
    for (const width of [1280, 768, 390, 360, 320]) {
      await page.setViewportSize({ width, height: width < 768 ? 844 : 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth), `${path} at ${width}px`).toBeLessThanOrEqual(width);
      if (width < 768) {
        const overflowing = await page.locator(".workspace-table-scroll, .clinical-calendar-grid, .tooth-row").evaluateAll((elements) => elements
          .filter((element) => element.getClientRects().length > 0 && element.scrollWidth > element.clientWidth + 1)
          .map((element) => `${element.className}: ${element.scrollWidth}/${element.clientWidth}`));
        expect(overflowing, `Scroll horizontal interno en ${path} a ${width}px`).toEqual([]);
      }
      if (capturePaths.includes(path) && width !== 768) {
        const slug = path.replace(/^\/app\/?/, "").replaceAll("/", "-") || "inicio";
        await page.screenshot({ path: `.e2e-closure-artifacts/route-${slug}-${width}.png`, fullPage: true });
      }
    }
  }
  await page.setViewportSize({ width: 1280, height: 720 });
}

test("flujo clínico completo de React contra la API", async ({ page }) => {
  test.setTimeout(180_000);
  const unique = String(Date.now()).slice(-9);
  const phone = `9${unique}`;
  const name = `E2E${unique}`;

  await page.goto("login");
  await captureFormVariants(page, "redesign-login");
  await expectTabSequence(page, [
    page.getByLabel("Usuario"),
    page.getByLabel("Contraseña", { exact: true }),
    page.getByRole("button", { name: "Mostrar contraseña" }),
    page.getByRole("link", { name: "¿Olvidaste tu contraseña?" }),
    page.getByRole("button", { name: "Iniciar sesión" }),
  ]);
  await page.getByLabel("Usuario").fill("e2e_doctor");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByText(/Bienvenido, Dr. E2E_DOCTOR/)).toBeVisible();
  await page.getByRole("link", { name: "Aviso de Privacidad" }).click();
  await expect(
    page.getByRole("heading", { name: /Aviso de Privacidad/ }),
  ).toBeVisible();
  await captureFormVariants(page, "redesign-privacy");

  let failDashboardOnce = true;
  await page.route("**/api/v1/clinics/dashboard/", async (route) => {
    if (failDashboardOnce) {
      failDashboardOnce = false;
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Agenda temporalmente no disponible." }) });
      return;
    }
    await route.continue();
  });
  await page.goto("/app/");
  await expect(page.getByRole("alert")).toContainText("Agenda temporalmente no disponible.");
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("heading", { name: /Bienvenido, Dr. E2E_DOCTOR/ })).toBeVisible();
  await page.unroute("**/api/v1/clinics/dashboard/");

  await page
    .getByRole("link", { name: /Pacientes/ })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Gestión de pacientes" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Acceder a Registrar paciente" }).click();
  await expectTabSequence(page, [
    page.getByLabel("Nombre"),
    page.getByLabel("Apellido paterno"),
    page.getByLabel("Apellido materno"),
  ]);
  await captureFormVariants(page, "redesign-patient-form");
  await page.getByLabel("Nombre").fill(name);
  await page.getByLabel("Apellido paterno").fill("PRUEBA");
  await page.getByLabel("Apellido materno").fill("REACT");
  await page.getByLabel("Fecha de nacimiento").fill("1990-01-01");
  await page.getByLabel("Género").selectOption("F");
  await page.getByLabel("Teléfono").fill(phone);
  await page
    .getByLabel("Correo electrónico")
    .fill(`${name.toLowerCase()}@example.com`);
  await expectResponsiveWidths(page);
  let rejectPatientCreate = true;
  await page.route("**/api/v1/clinics/patients/", async (route) => {
    if (route.request().method() === "POST" && rejectPatientCreate) {
      rejectPatientCreate = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          telefono: ["El teléfono no está disponible."],
          detail: "Revisa los datos del paciente.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Registrar paciente" }).click();
  const phoneInput = page.getByLabel("Teléfono");
  await expect(phoneInput).toHaveAttribute("aria-invalid", "true");
  await expect(phoneInput).toHaveAttribute("aria-describedby", "telefono-help telefono-error");
  await expect(page.locator("#telefono-error")).toHaveText("El teléfono no está disponible.");
  await expect(page.getByRole("alert")).toHaveText("Revisa los datos del paciente.");
  await page.getByRole("button", { name: "Registrar paciente" }).click();
  await page.unroute("**/api/v1/clinics/patients/");
  await expect(
    page.getByRole("heading", { name: new RegExp(name) }),
  ).toBeVisible();
  const patientId = page.url().match(/patients\/(\d+)/)?.[1];
  expect(patientId).toBeTruthy();
  await page.route(`**/api/v1/clinics/patients/${patientId}/`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Paciente temporalmente no disponible." }) });
      return;
    }
    await route.continue();
  });
  await page.reload();
  await expect(page.getByRole("alert")).toHaveText("Paciente temporalmente no disponible.");
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/`);
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("heading", { name: new RegExp(name) })).toBeVisible();
  await expectResponsiveWidths(page);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-patient-detail-desktop.png", fullPage: true });
  await page.getByRole("link", { name: "Nueva cita" }).click();
  await expect(page.getByText("Paciente seleccionado")).toBeVisible();
  await expect(page.getByText(new RegExp(name)).first()).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("heading", { name: new RegExp(name) })).toBeVisible();

  await page.goto(`/app/patients/${patientId}/record`);
  await expect(page.getByRole("heading", { name: "Resumen clínico" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Secciones del expediente" })).toContainText(`${name} PRUEBA REACT`);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(async () => (await page.locator(".workspace-sidebar").boundingBox()).x)
    .toBeLessThan(-200);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-patient-workspace-mobile.png", fullPage: true });
  for (const width of [320, 375, 390, 430, 768]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(`/app/patients/${patientId}/consent`);
    const nav = page.getByRole("navigation", { name: "Secciones del expediente" });
    const links = nav.locator(".patient-workspace-links");
    const active = nav.getByRole("link", { name: "Consentimiento" });
    await expect(active).toHaveAttribute("aria-current", "page");
    await expect.poll(() => active.evaluate((element) => {
      const container = element.parentElement.getBoundingClientRect();
      const item = element.getBoundingClientRect();
      return item.left >= container.left && item.right <= container.right;
    })).toBe(true);
    const metrics = await links.evaluate((element) => ({
      display: getComputedStyle(element).display, wrap: getComputedStyle(element).flexWrap,
      overflow: getComputedStyle(element).overflowX, scrollbar: getComputedStyle(element).scrollbarWidth,
      tops: new Set([...element.querySelectorAll("a")].map((link) => link.offsetTop)).size,
      lastWidth: element.lastElementChild.getBoundingClientRect().width,
      lastScrollWidth: element.lastElementChild.scrollWidth,
      documentWidth: document.documentElement.scrollWidth,
    }));
    expect(metrics).toMatchObject({ display: "flex", wrap: "nowrap", overflow: "auto", scrollbar: "none", tops: 1 });
    expect(metrics.lastWidth).toBeGreaterThanOrEqual(metrics.lastScrollWidth);
    expect(metrics.documentWidth).toBeLessThanOrEqual(width);
    await expect(nav).toHaveAttribute("data-more", "false");
    await links.evaluate((element) => { element.scrollLeft = 0; });
    await expect(nav).toHaveAttribute("data-more", "true");
    await active.focus();
    await expect(active).toBeFocused();
  }
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.route(`**/api/v1/clinics/patients/${patientId}/`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "No se pudo cargar la edición." }) });
      return;
    }
    await route.continue();
  });
  await page.goto(`/app/patients/${patientId}/edit`);
  await expect(page.getByRole("alert")).toHaveText("No se pudo cargar la edición.");
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/`);
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("heading", { name: "Editar paciente" })).toBeVisible();
  await page.getByLabel("Nombre", { exact: true }).fill("BORRADOR");
  await page.getByRole("link", { name: "Resumen", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Cambios sin guardar" })).toBeVisible();
  await page.getByRole("dialog", { name: "Cambios sin guardar" }).getByRole("button", { name: "Volver" }).click();
  await expect(page.getByLabel("Nombre", { exact: true })).toHaveValue("BORRADOR");
  await page.getByRole("button", { name: "Salir", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Salir con cambios sin guardar" })).toBeVisible();
  await page.getByRole("dialog", { name: "Salir con cambios sin guardar" }).getByRole("button", { name: "Volver" }).click();
  await expect(page.getByLabel("Nombre", { exact: true })).toHaveValue("BORRADOR");
  await page.getByLabel("Nombre", { exact: true }).fill(name);
  await page.getByLabel("Apellido materno").fill("MIGRADO");
  await expectResponsiveWidths(page);
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(page.getByRole("heading", { name: /MIGRADO/ })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Secciones del expediente" })).toContainText(`${name} PRUEBA MIGRADO`);

  await page.goto(`/app/patients/search?q=${name}`);
  await expect(
    page.getByRole("cell", { name: `${name} PRUEBA MIGRADO`, exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Paginación de pacientes" })).toBeVisible();
  await expect(page.getByRole("link", { name: `Ver ${name}` })).toBeVisible();
  await expectResponsiveWidths(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("Desliza la tabla para ver todas las columnas")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-patient-list-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.goto(`/app/patients/${patientId}/medical-history`);
  await expect(page.locator("#problemas_cardiacos-unknown")).toBeChecked();
  await page.locator('label[for="tratamiento_medico-yes"]').click();
  await page.locator("#tratamiento_medico-yes").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#tratamiento_medico-no")).toBeChecked();
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator("#tratamiento_medico-yes")).toBeChecked();
  await page.getByLabel("Alergias").fill("NINGUNA");
  await expectResponsiveWidths(page);
  for (const label of ["Alergias", "Medicamentos", "Cirugías previas", "Otros"]) {
    await expect(page.getByLabel(label, { exact: true })).toBeVisible();
  }
  await captureFormVariants(page, "redesign-medical-history");
  let rejectHistorySave = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/medical-history/`, async (route) => {
    if (route.request().method() === "PUT" && rejectHistorySave) {
      rejectHistorySave = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          tratamiento_medico: ["Confirma la respuesta al antecedente."],
          detail: "No se pudo guardar el antecedente.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Guardar antecedentes" }).click();
  await expect(page.getByRole("alert")).toHaveText("No se pudo guardar el antecedente.");
  const treatmentAnswer = page.locator("#tratamiento_medico-yes");
  await expect(treatmentAnswer).toHaveAttribute("aria-invalid", "true");
  await expect(treatmentAnswer).toHaveAttribute("aria-describedby", "tratamiento_medico-error");
  await expect(page.locator("#tratamiento_medico-error")).toHaveText("Confirma la respuesta al antecedente.");
  await expect(page.getByLabel("Alergias")).toHaveValue("NINGUNA");
  await page.getByRole("button", { name: "Guardar antecedentes" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/medical-history/`);
  await expect(page.getByText("Antecedentes actualizados")).toBeVisible();

  await page.goto(`/app/patients/${patientId}/consultations/new`);
  await expectTabSequence(page, [
    page.getByLabel("Motivo de consulta"),
    page.getByLabel("Diagnóstico"),
    page.getByLabel("Tratamiento"),
  ]);
  await page.getByLabel("Motivo de consulta").fill("CONTROL E2E");
  await page.getByLabel("Diagnóstico").fill("DIAGNOSTICO E2E");
  await page.getByLabel("Tratamiento").fill("TRATAMIENTO E2E");
  await expectResponsiveWidths(page);
  await captureFormVariants(page, "redesign-consultation-form");
  let rejectConsultationCreate = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/consultations/**`, async (route) => {
    if (route.request().method() === "POST" && rejectConsultationCreate) {
      rejectConsultationCreate = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          motivo_consulta: ["Revisa el motivo de consulta."],
          detail: "No se pudo guardar la consulta.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Registrar consulta" }).click();
  const consultationReason = page.getByLabel("Motivo de consulta");
  await expect(consultationReason).toHaveAttribute("aria-invalid", "true");
  await expect(consultationReason).toHaveAttribute("aria-describedby", "motivo_consulta-error");
  await expect(page.locator("#motivo_consulta-error")).toHaveText("Revisa el motivo de consulta.");
  await expect(page.getByRole("alert")).toHaveText("No se pudo guardar la consulta.");
  await page.getByRole("button", { name: "Registrar consulta" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/consultations/**`);
  await expect(
    page.getByRole("heading", { name: "Receta médica" }),
  ).toBeVisible();
  await expect(page.getByText("DIAGNOSTICO E2E")).toBeVisible();
  const prescriptionPath = new URL(page.url()).pathname;
  await page.evaluate(() => { window.__printCalled = false; window.print = () => { window.__printCalled = true; }; });
  await page.getByRole("button", { name: "Descargar PDF / Imprimir" }).click();
  expect(await page.evaluate(() => window.__printCalled)).toBe(true);
  await page.emulateMedia({ media: "print" });
  await expect(page.getByRole("button", { name: "Descargar PDF / Imprimir", includeHidden: true })).toBeHidden();
  await page.emulateMedia({ media: "screen" });
  await captureFormVariants(page, "redesign-prescription");

  await page.goto(`/app/patients/${patientId}/consultations`);
  await expect(page.getByRole("list", { name: "Consultas registradas para este paciente" }).getByRole("heading", { name: "CONTROL E2E" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Ver receta de la consulta/ })).toHaveAttribute("href", /\/consultations\/\d+\/prescription/);
  await expectResponsiveWidths(page);
  await captureFormVariants(page, "redesign-consultation-timeline");

  await page.goto(`/app/patients/${patientId}/images/upload`);
  await expectTabSequence(page, [
    page.getByLabel("Consulta"),
    page.getByLabel("Tipo de imagen"),
    page.getByLabel("Descripción"),
    page.getByLabel("Archivo"),
  ]);
  await page.getByLabel("Consulta").selectOption({ index: 1 });
  await page.getByLabel("Tipo de imagen").fill("RADIOGRAFIA");
  await page.getByLabel("Descripción").fill("IMAGEN E2E");
  await page.getByLabel("Archivo").setInputFiles(tinyImage);
  await expectResponsiveWidths(page);
  await captureFormVariants(page, "redesign-clinical-image-upload");
  let rejectImageUpload = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/clinical-images/`, async (route) => {
    if (route.request().method() === "POST" && rejectImageUpload) {
      rejectImageUpload = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ imagen: ["El formato de imagen no es válido."], detail: "No se pudo guardar la imagen." }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Cargar imagen" }).click();
  const imageInput = page.getByLabel("Archivo");
  await expect(imageInput).toHaveAttribute("aria-invalid", "true");
  await expect(imageInput).toHaveAttribute("aria-describedby", "imagen-error");
  await expect(page.locator("#imagen-error")).toHaveText("El formato de imagen no es válido.");
  await expect(page.getByRole("alert")).toHaveText("No se pudo guardar la imagen.");
  await page.getByRole("button", { name: "Cargar imagen" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/clinical-images/`);
  await page.waitForURL(new RegExp(`patients/${patientId}/images/history$`));
  await expect(page.getByText("IMAGEN E2E")).toBeVisible();
  const uploadedDate = (await page.locator(".clinical-image-list time").getAttribute("datetime")).slice(0, 10);
  await expect(page.getByRole("link", { name: "Descargar" })).toBeVisible();
  const clinicalImageDownload = page.waitForEvent("download");
  await page.getByRole("link", { name: "Descargar" }).click();
  expect((await clinicalImageDownload).suggestedFilename()).toMatch(/\.png$/i);
  await captureFormVariants(page, "redesign-clinical-images-history");
  await expectResponsiveWidths(page);
  await page.goto(`/app/patients/${patientId}/images`);
  await expect(
    page.getByRole("heading", { name: "Imágenes clínicas" }),
  ).toBeVisible();
  let failConsultationFilterOnce = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/consultations/**`, async (route) => {
    if (failConsultationFilterOnce) {
      failConsultationFilterOnce = false;
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Consultas no disponibles." }) });
      return;
    }
    await route.continue();
  });
  await page.getByRole("heading", { name: "Buscar imágenes" }).click();
  await expect(page.getByRole("alert")).toContainText("No se pudieron cargar las consultas.");
  await expect(page.getByText("IMAGEN E2E")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-images-partial-390.png", fullPage: true });
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.getByRole("button", { name: "Reintentar consultas" }).click();
  await expect(page.getByLabel("Consulta").locator("option")).toHaveCount(2);
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/consultations/**`);
  await page.getByLabel("Fecha").fill(uploadedDate);
  await expect(page.getByText("IMAGEN E2E")).toBeVisible();
  await page.getByLabel("Consulta").selectOption({ index: 1 });
  await expect(page.getByText("IMAGEN E2E")).toBeVisible();
  await captureFormVariants(page, "redesign-clinical-images-search");
  await expectResponsiveWidths(page);

  await page.goto(`/app/patients/${patientId}/odontogram`);
  await expect(page.locator(".odontogram-summary dt", { hasText: "Sanos" }).locator("..").locator("dd")).toHaveText("0");
  await page.getByRole("button", { name: "Caries", exact: true }).click();
  await page.getByRole("button", { name: "18 oclusal sin registrar" }).click();
  let failOdontogramSaveOnce = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/odontogram/`, async (route) => {
    if (route.request().method() === "PUT" && failOdontogramSaveOnce) {
      failOdontogramSaveOnce = false;
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "No se pudo guardar el odontograma." }) });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Guardar odontograma" }).click();
  await expect(page.getByRole("alert")).toContainText("No se pudo guardar el odontograma.");
  await page.getByRole("button", { name: "Guardar odontograma" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/odontogram/`);
  await expect(
    page.getByText("Odontograma guardado correctamente."),
  ).toBeVisible();
  await expect(page.locator(".clinical-toast.is-success")).toContainText("Odontograma guardado correctamente.");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(async () => (await page.locator(".clinical-toast.is-success").boundingBox()).y).toBeGreaterThan(700);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-toast-mobile.png" });
  await page.setViewportSize({ width: 1280, height: 720 });
  await expect(page.locator(".odontogram-summary dt", { hasText: "Caries" }).locator("..").locator("dd")).toHaveText("1");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("button", { name: "Limpiar todo" }).click();
  await expect(page.locator(".odontogram-summary dt", { hasText: "Caries" }).locator("..").locator("dd")).toHaveText("1");
  await expectResponsiveWidths(page);
  const toothTarget = await page.getByRole("button", { name: "18 oclusal caries" }).boundingBox();
  expect(toothTarget.width).toBeGreaterThanOrEqual(24);
  expect(toothTarget.height).toBeGreaterThanOrEqual(24);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".odontogram-quadrants").first().locator(".odontogram-quadrant:visible")).toHaveCount(1);
  const mobileToothTarget = await page.getByRole("button", { name: "18 oclusal caries" }).boundingBox();
  expect(mobileToothTarget.width).toBeGreaterThanOrEqual(32);
  expect(mobileToothTarget.height).toBeGreaterThanOrEqual(32);
  await page.locator(".odontogram-quadrant-tabs").first().getByRole("button", { name: "Superior izquierda" }).click();
  await expect(page.locator(".odontogram-quadrants").first().locator(".odontogram-quadrant:visible h3")).toHaveText("Superior izquierda");
  expect(await page.locator(".odontogram-quadrants").first().evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(" ").length)).toBe(1);
  expect(await page.locator(".odontogram-summary").evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(" ").length)).toBe(2);
  const quadrantRow = page.locator(".odontogram-quadrant .tooth-row").first();
  expect(await quadrantRow.evaluate((element) => element.scrollWidth)).toBeLessThanOrEqual(await quadrantRow.evaluate((element) => element.clientWidth));
  await page.setViewportSize({ width: 1280, height: 720 });
  await expect.poll(() => page.locator(".odontogram-quadrant .tooth-row").evaluateAll((rows) => rows.filter((row) => row.scrollWidth > row.clientWidth + 1).length)).toBe(0);
  expect(await page.locator(".odontogram-quadrant .tooth-row").first().locator(".tooth").evaluateAll((teeth) => new Set(teeth.map((tooth) => tooth.getBoundingClientRect().top)).size)).toBe(1);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-odontogram-desktop.png", fullPage: true });
  await captureFormVariants(page, "redesign-odontogram");

  await page.goto(`/app/patients/${patientId}/comparative-study`);
  await expectTabSequence(page, [
    page.getByLabel("Diagnóstico"),
    page.getByLabel("Observaciones"),
    page.getByLabel("Oclusal superior"),
  ]);
  await page.getByLabel("Fecha de inicio").fill("2026-01-01");
  await page.getByLabel("Diagnóstico").fill("ESTUDIO E2E");
  await expectResponsiveWidths(page);
  for (const label of [
    "Oclusal superior",
    "Lateral izquierda",
    "Frontal",
    "Lateral derecha",
    "Oclusal inferior",
  ]) {
    await page.getByLabel(label, { exact: true }).setInputFiles(tinyImage);
  }
  await captureFormVariants(page, "redesign-comparative-study");
  await expect(page.getByRole("alert")).toHaveCount(0);
  let rejectStudySave = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/comparative-study/`, async (route) => {
    if (route.request().method() === "PUT" && rejectStudySave) {
      rejectStudySave = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ antes_frontal: ["La imagen frontal no es válida."], detail: "No se pudo guardar el estudio." }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Guardar estudio" }).click();
  const frontalImage = page.getByLabel("Frontal", { exact: true });
  await expect(frontalImage).toHaveAttribute("aria-invalid", "true");
  await expect(frontalImage).toHaveAttribute("aria-describedby", "antes_frontal-error");
  await expect(page.locator("#antes_frontal-error")).toHaveText("La imagen frontal no es válida.");
  await expect(page.getByRole("alert")).toHaveText("No se pudo guardar el estudio.");
  await page.getByRole("button", { name: "Guardar estudio" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/comparative-study/`);
  await expect(page.getByText("Estudio guardado correctamente.")).toBeVisible();
  const pdfPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: /Descargar PDF/ }).click();
  expect((await pdfPromise).suggestedFilename()).toMatch(/^Estudio_.*\.pdf$/);

  await page.goto(`/app/patients/${patientId}/consent`);
  await page.getByLabel("He leído y acepto los términos.").check();
  await expectTabSequence(page, [
    page.getByLabel("He leído y acepto los términos."),
    page.getByLabel("Identificación oficial"),
  ]);
  await page.getByLabel("Identificación oficial").setInputFiles(tinyImage);
  await expectResponsiveWidths(page);
  await captureFormVariants(page, "redesign-consent-form");
  let rejectConsentSave = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/consent/`, async (route) => {
    if (route.request().method() === "POST" && rejectConsentSave) {
      rejectConsentSave = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ archivo_ine: ["La identificación no se pudo validar."] }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Aceptar y guardar" }).click();
  const identityInput = page.getByLabel("Identificación oficial");
  await expect(identityInput).toHaveAttribute("aria-invalid", "true");
  await expect(identityInput).toHaveAttribute("aria-describedby", "ine-help ine-error");
  await expect(page.locator("#ine-error")).toHaveText("La identificación no se pudo validar.");
  await page.getByRole("button", { name: "Aceptar y guardar" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/consent/`);
  await expect(
    page.getByRole("heading", { name: "Consentimiento aceptado" }),
  ).toBeVisible();

  let rejectDiagnosticsList = true;
  await page.route("**/api/v1/clinics/diagnostics/**", async (route) => {
    if (rejectDiagnosticsList) {
      rejectDiagnosticsList = false;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Diagnósticos temporalmente no disponibles." }),
      });
      return;
    }
    await route.continue();
  });
  await page.goto("/app/diagnostics");
  await expect(page.getByRole("alert")).toContainText("Diagnósticos temporalmente no disponibles.");
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByLabel("Paciente")).toBeVisible();
  await page.unroute("**/api/v1/clinics/diagnostics/**");
  await page.getByLabel("Paciente").fill(name);
  await page.getByLabel("Tipo").fill("RADIOGRAFIA");
  await page.getByLabel("Fecha").fill(uploadedDate);
  await page.getByRole("button", { name: "Filtrar" }).click();
  const diagnosticParams = new URL(page.url()).searchParams;
  expect(diagnosticParams.get("patient")).toBe(name);
  expect(diagnosticParams.get("type")).toBe("RADIOGRAFIA");
  expect(diagnosticParams.get("date")).toBe(uploadedDate);
  await expect(
    page.getByRole("cell", { name: `${name} PRUEBA`, exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByRole("cell", { name: "Pendiente", exact: true })).toBeVisible();
  await captureFormVariants(page, "redesign-diagnostics-list");
  await expectResponsiveWidths(page);
  const diagnosticLink = page.getByRole("link", { name: "Analizar" });
  const diagnosticImageId = (await diagnosticLink.getAttribute("href")).match(/diagnostics\/(\d+)/)?.[1];
  let failDiagnosticImageLoadOnce = true;
  await page.route(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/`, async (route) => {
    if (failDiagnosticImageLoadOnce) {
      failDiagnosticImageLoadOnce = false;
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Imagen temporalmente no disponible." }) });
      return;
    }
    await route.continue();
  });
  await diagnosticLink.click();
  const diagnosticResultPath = new URL(page.url()).pathname;
  await expect(
    page.getByRole("heading", { name: /Resultados de análisis/ }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Imagen temporalmente no disponible.");
  await page.getByRole("button", { name: "Reintentar" }).click();
  await page.unroute(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/`);
  await page.getByRole("button", { name: "Analizar imagen" }).click();
  await expect(page.getByText("Procesando imagen con YOLO…")).toBeHidden({
    timeout: 30_000,
  });
  await expect(page.getByText("Imagen analizada")).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.route(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/analyze/`, async (route) => {
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "El análisis no está disponible." }) });
  });
  await page.getByRole("button", { name: "Analizar nuevamente" }).click();
  await expect(page.getByRole("alert")).toContainText("El análisis no está disponible.");
  await page.unroute(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/analyze/`);
  await page.getByRole("button", { name: "Analizar nuevamente" }).click();
  await expect(page.getByText("Procesando imagen con YOLO…")).toBeHidden({ timeout: 30_000 });
  await expect(page.locator("#main-content [role='alert']")).toHaveCount(0);
  await expect(page.locator(".image-viewer")).toHaveCount(2);
  const zoomControl = page.getByRole("region", { name: "Imagen original" }).getByRole("button", { name: "Acercar" });
  await zoomControl.focus();
  await expect(zoomControl).toBeFocused();
  await zoomControl.press("Space");
  await expect(page.getByRole("region", { name: "Imagen analizada" }).getByRole("button", { name: "Alejar" })).toBeVisible();
  await expect.poll(async () =>
    page.locator(".image-viewer img[src]").evaluateAll((images) =>
      images.length > 0 && images.every((image) => image.complete && image.naturalWidth > 0),
    ),
    { timeout: 15_000 },
  ).toBe(true);
  await expectResponsiveWidths(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("Desliza la tabla para ver todas las columnas")).toBeHidden();
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-diagnostic-desktop.png", fullPage: true });
  await captureFormVariants(page, "redesign-diagnostic-viewer");

  await expectRoutesAtAllWidths(page, [
    "/app/", "/app/privacy", "/app/patients", "/app/patients/list", "/app/patients/search",
    "/app/patients/new", "/app/patients/contact", `/app/patients/${patientId}`,
    `/app/patients/${patientId}/edit`, "/app/clinical-record", `/app/patients/${patientId}/record`,
    `/app/patients/${patientId}/medical-history`, `/app/patients/${patientId}/consultations/new`,
    `/app/patients/${patientId}/consultations`, prescriptionPath, `/app/patients/${patientId}/images`,
    `/app/patients/${patientId}/images/upload`, `/app/patients/${patientId}/images/search`,
    `/app/patients/${patientId}/images/history`, `/app/patients/${patientId}/odontogram`,
    `/app/patients/${patientId}/comparative-study`, `/app/patients/${patientId}/consent`,
    "/app/exports", "/app/diagnostics", diagnosticResultPath,
  ], [
    "/app/patients", "/app/patients/list", "/app/clinical-record", `/app/patients/${patientId}`,
    `/app/patients/${patientId}/record`,
    `/app/patients/${patientId}/images`,
  ]);

  await page.goto(`/app/patients/${patientId}/images/history`);
  await page.route(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/`, async (route) => {
    if (route.request().method() === "DELETE") {
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "El borrado no está disponible." }) });
      return;
    }
    await route.continue();
  });
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Eliminar" }).click();
  await expect(page.getByRole("alert")).toContainText("No se pudo eliminar la imagen.");
  await expect(page.getByText("IMAGEN E2E")).toBeVisible();
  await page.unroute(`**/api/v1/clinics/clinical-images/${diagnosticImageId}/`);
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Eliminar" }).click();
  await expect(page.getByText("No hay imágenes clínicas.")).toBeVisible();

  await page.goto("/app/exports");
  await expectResponsiveWidths(page);
  await captureFormVariants(page, "redesign-exports");
  const exportNames = [
    "Pacientes.xlsx",
    "Consultas.xlsx",
    "ImagenesClinicas.xlsx",
  ];
  for (const filename of exportNames) {
    const downloadPromise = page.waitForEvent("download");
    await page
      .getByRole("link", { name: "Descargar Excel" })
      .nth(exportNames.indexOf(filename))
      .click();
    expect((await downloadPromise).suggestedFilename()).toBe(filename);
  }

  await page.goto("/app/patients/contact");
  await page.getByLabel("Buscar paciente por nombre").fill(name);
  await expect(page.getByRole("button", { name: new RegExp(name) })).toBeVisible();
  await expectTabSequence(page, [
    page.getByLabel("Buscar paciente por nombre"),
    page.getByRole("button", { name: new RegExp(name) }),
  ]);
  await page.getByRole("button", { name: new RegExp(name) }).click();
  await expectTabSequence(page, [
    page.getByLabel("Asunto"),
    page.getByLabel("Mensaje"),
    page.getByRole("button", { name: "Enviar correo" }),
  ]);
  await page.getByLabel("Asunto").fill("MENSAJE E2E");
  await expectResponsiveWidths(page);
  await page.getByLabel("Mensaje").fill("VALIDACION DE CORREO");
  await expect(page.getByRole("button", { name: "Cambiar paciente" })).toBeVisible();
  await captureFormVariants(page, "redesign-patient-contact");
  let rejectEmail = true;
  await page.route(`**/api/v1/clinics/patients/${patientId}/email/`, async (route) => {
    if (route.request().method() === "POST" && rejectEmail) {
      rejectEmail = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          asunto: ["Revisa el asunto del correo."],
          detail: "No se pudo enviar el mensaje.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Enviar correo" }).click();
  const emailSubject = page.getByLabel("Asunto");
  await expect(emailSubject).toHaveAttribute("aria-invalid", "true");
  await expect(emailSubject).toHaveAttribute("aria-describedby", "subject-error");
  await expect(page.locator("#subject-error")).toHaveText("Revisa el asunto del correo.");
  await expect(page.getByRole("alert")).toHaveText("No se pudo enviar el mensaje.");
  await page.getByRole("button", { name: "Enviar correo" }).click();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/email/`);
  await expect(page.getByText(/Correo enviado correctamente/)).toBeVisible();

  await page.getByRole("link", { name: /Citas/ }).click();
  await page.getByRole("link", { name: /Nueva cita/ }).click();
  await page.getByLabel("Buscar paciente por nombre").fill(name);
  await expect(page.getByRole("button", { name: new RegExp(name) })).toBeVisible();
  await expectTabSequence(page, [
    page.getByLabel("Buscar paciente por nombre"),
    page.getByRole("button", { name: new RegExp(name) }),
  ]);
  await page.getByRole("button", { name: new RegExp(name) }).click();
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  await page.getByLabel("Fecha").fill(tomorrow.toISOString().slice(0, 10));
  await page.getByLabel("Hora").fill("10:00");
  await page.getByLabel("Motivo").fill("Control E2E");
  await expect(page.getByLabel("Fecha")).toHaveAttribute("required", "");
  await expect(page.getByLabel("Hora")).toHaveAttribute("required", "");
  await captureFormVariants(page, "redesign-appointment-form");
  await page.getByLabel("Estado").focus();
  await expectTabSequence(page, [
    page.getByLabel("Estado"),
    page.getByLabel("Motivo"),
    page.getByLabel("Observaciones"),
  ]);
  await expectResponsiveWidths(page);
  let rejectAppointmentCreate = true;
  await page.route("**/api/v1/clinics/appointments/", async (route) => {
    if (route.request().method() === "POST" && rejectAppointmentCreate) {
      rejectAppointmentCreate = false;
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          fecha: ["La fecha no está disponible."],
          detail: "Revisa la programación.",
        }),
      });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Registrar cita" }).click();
  const dateInput = page.getByLabel("Fecha");
  await expect(dateInput).toHaveAttribute("aria-invalid", "true");
  await expect(dateInput).toHaveAttribute("aria-describedby", "fecha-error");
  await expect(page.locator("#fecha-error")).toHaveText("La fecha no está disponible.");
  await expect(page.getByRole("alert").filter({ hasText: "Revisa la programación." })).toBeVisible();
  await page.getByRole("button", { name: "Registrar cita" }).click();
  await page.unroute("**/api/v1/clinics/appointments/");
  await expect(
    page.getByRole("heading", { name: /Detalle de cita/ }),
  ).toBeVisible();
  await expect(page.getByText("Control E2E")).toBeVisible();
  const appointmentId = page.url().match(/appointments\/(\d+)/)?.[1];

  let failAppointmentEditLoadOnce = true;
  await page.route(`**/api/v1/clinics/appointments/${appointmentId}/`, async (route) => {
    if (route.request().method() === "GET" && failAppointmentEditLoadOnce) {
      failAppointmentEditLoadOnce = false;
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Cita temporalmente no disponible." }) });
      return;
    }
    await route.continue();
  });
  await page.goto(`/app/appointments/${appointmentId}/edit`);
  await expect(page.getByRole("alert")).toContainText("Cita temporalmente no disponible.");
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("heading", { name: "Editar cita" })).toBeVisible();
  await page.unroute(`**/api/v1/clinics/appointments/${appointmentId}/`);
  await page.getByLabel("Motivo").fill("Control E2E editado");
  await expectResponsiveWidths(page);
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(page.getByText("Control E2E editado")).toBeVisible();

  await page.goto("/app/appointments");
  await expect(
    page.getByRole("region", { name: "Calendario de citas" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Completar" }).last().click();
  await expect(page.getByText("Completada").last()).toBeVisible();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-calendar-desktop.png", fullPage: true });

  await page.goto("/app/appointments/new");
  await page.getByLabel("Buscar paciente por nombre").fill(name);
  await page.getByRole("button", { name: new RegExp(name) }).click();
  await page.getByLabel("Fecha").fill(tomorrow.toISOString().slice(0, 10));
  await page.getByLabel("Hora").fill("11:00");
  await page.getByLabel("Motivo").fill("Cancelación E2E");
  await page.getByRole("button", { name: "Registrar cita" }).click();
  await expect(page.getByRole("heading", { name: /Detalle de cita/ })).toBeVisible();
  await page.goto("/app/appointments");
  await page.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByRole("dialog", { name: "Cancelar cita" })).toBeVisible();
  await page.getByRole("button", { name: "Sí, cancelar cita" }).click();
  await expect(page.getByText("Cancelada").last()).toBeVisible();
  await page.route("**/api/v1/clinics/appointments/**", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (route.request().method() === "GET" && requestUrl.pathname === "/api/v1/clinics/appointments/" && requestUrl.searchParams.get("status") === "A") {
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "No se pudieron actualizar las citas." }) });
      return;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Canceladas" }).click();
  const appointmentError = page.getByRole("alert").filter({ hasText: "No se pudieron actualizar las citas." });
  await expect(appointmentError).toBeVisible();
  await page.unroute("**/api/v1/clinics/appointments/**");
  await appointmentError.getByRole("button", { name: "Reintentar" }).click();
  // List and calendar are independent queries with their own retry controls.
  const calendarError = page.getByRole("alert").filter({ hasText: "No se pudo cargar el calendario." });
  await calendarError.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.locator("#main-content [role='alert']")).toHaveCount(0);
  await page.goto(`/app/appointments?status=A&search=${encodeURIComponent(name)}`);
  await expect(page.getByRole("button", { name: "Canceladas" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Buscar citas")).toHaveValue(name);
  await expect(page.getByRole("cell", { name: "Cancelación E2E", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Completar" })).toHaveCount(0);
  await expectResponsiveWidths(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Agenda", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Mes", exact: true })).toHaveAttribute("aria-pressed", "false");
  await page.getByRole("button", { name: "Mes", exact: true }).click();
  await expect(page.getByText("Desliza el calendario para ver toda la semana")).toBeHidden();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-appointments-month-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Agenda", exact: true }).click();
  await expect(page.getByRole("button", { name: "Agenda", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Desliza el calendario para ver toda la semana")).toBeHidden();
  await expect(page.getByText("Desliza la tabla para ver todas las columnas")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-appointments-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1280, height: 720 });

  await expectRoutesAtAllWidths(page, [
    "/app/appointments", "/app/appointments/new", `/app/appointments/${appointmentId}`,
    `/app/appointments/${appointmentId}/edit`,
  ], [`/app/appointments/${appointmentId}`]);

  await page.goto("/app/patients/search?q=E2E_NO_MATCH_987654321");
  await expect(page.getByText("No se encontraron pacientes.")).toBeVisible();

  await page.goto(`/app/patients/${patientId}`);
  await page.route(`**/api/v1/clinics/patients/${patientId}/deactivate/`, async (route) => {
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "No se pudo desactivar al paciente." }) });
  });
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Desactivar" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "No se pudo desactivar al paciente." })).toBeVisible();
  await page.unroute(`**/api/v1/clinics/patients/${patientId}/deactivate/`);
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Desactivar" }).click();
  await expect(page).toHaveURL(/patients\/search/);

  await page.getByRole("button", { name: /Salir/ }).click();
  await expect(page).toHaveURL(/\/app\/login$/);
  await page.goto("/app/patients/search?q=E2E_NO_MATCH_987654321");
  await expect(page).toHaveURL(/\/app\/login$/);
  await page.getByLabel("Usuario").fill("e2e_doctor");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app\/patients\/search\?q=E2E_NO_MATCH_987654321$/);
  await expect(page.getByLabel("Buscar pacientes")).toHaveValue("E2E_NO_MATCH_987654321");

  await page.getByRole("button", { name: /Salir/ }).click();
  await page.getByLabel("Usuario").fill("e2e_other_doctor");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.locator(".workspace-user-name")).toHaveText("e2e_other_doctor");
  await page.goto("/app/patients/list");
  await expect(page.getByRole("heading", { name: "Todos los pacientes" })).toBeVisible();
  await expect(page.getByText(name, { exact: false })).toHaveCount(0);
  await page.goto(`/app/patients/${patientId}`);
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("heading", { name: new RegExp(name) })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Secciones del expediente" })).not.toContainText(name);
});

test("navegación móvil conserva el menú clínico", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("login");
  for (const width of [390, 768]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1024 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByLabel("Usuario").fill("e2e_doctor");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(
    page.getByRole("heading", { name: "Bienvenido, Dr. E2E_DOCTOR" }),
  ).toBeVisible();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-dashboard-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(async () => (await page.locator(".workspace-sidebar").boundingBox()).x)
    .toBeLessThan(-200);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  const dashboardTableHint = page.getByText("Desliza la tabla para ver todas las columnas").first();
  if (await dashboardTableHint.count()) await expect(dashboardTableHint).toBeHidden();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-dashboard-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Abrir navegación" }).click();
  await expect(page.getByRole("link", { name: /Pacientes/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Diagnósticos/ })).toBeVisible();
  await expect
    .poll(async () => (await page.locator(".workspace-sidebar").boundingBox()).x)
    .toBe(0);
  await expect(page.getByRole("link", { name: "Inicio", exact: true })).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(page.getByRole("link", { name: "Exportaciones" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Inicio", exact: true })).toBeFocused();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-navigation-mobile.png", fullPage: true });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Abrir navegación" })).toBeFocused();
  await expect(page.getByRole("button", { name: "Abrir navegación" })).toHaveAttribute("aria-expanded", "false");
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page.getByRole("button", { name: "Abrir navegación" })).toBeVisible();
  await expect
    .poll(async () => (await page.locator(".workspace-sidebar").boundingBox()).x)
    .toBeLessThan(-200);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(768);
  await expect(page.getByText("Desliza la tabla para ver todas las columnas")).toBeHidden();
  await expect(page.getByRole("link", { name: "Abrir agenda" })).toBeInViewport();
  await page.screenshot({ path: ".e2e-closure-artifacts/redesign-dashboard-tablet.png", fullPage: true });
});

test("el listado de pacientes informa el error y permite reintentar", async ({ page }) => {
  await page.goto("login");
  await page.getByLabel("Usuario").fill("e2e_doctor");
  await page.getByLabel("Contraseña", { exact: true }).fill("e2e_password_123");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByRole("heading", { name: "Bienvenido, Dr. E2E_DOCTOR" })).toBeVisible();

  // This scenario must not depend on a patient created by a previous test.
  const session = await (await page.request.get('/api/v1/auth/session/')).json();
  const memberships = await (await page.request.get('/api/v1/clinics/memberships/', { headers: { Authorization: `Bearer ${session.access}` } })).json();
  const unique = String(Date.now()).slice(-8);
  const created = await page.request.post('/api/v1/clinics/patients/', { headers: { Authorization: `Bearer ${session.access}`, 'X-Clinic-ID': memberships[0].id }, data: { nombre: 'REINTENTO', appat: 'PRUEBA', apmat: 'DEMO', fecha_nacimiento: '1990-01-01', genero: 'F', telefono: `44${unique}`, email: `retry-${unique}@example.test` } });
  expect(created.status()).toBe(201);

  let shouldFail = true;
  await page.route("**/api/v1/clinics/patients/**", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (shouldFail && requestUrl.pathname === "/api/v1/clinics/patients/") {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Servicio temporalmente no disponible" }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/app/patients/list");
  await expect(page.getByRole("alert")).toBeVisible();
  shouldFail = false;
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("table")).toBeVisible();
});
