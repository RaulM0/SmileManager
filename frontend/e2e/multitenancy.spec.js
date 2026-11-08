import { expect, test } from '@playwright/test';

async function login(page, username) {
  await page.goto('/app/login');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Contraseña', { exact: true }).fill('e2e_password_123');
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
}

async function navigateWithinApp(page, path) {
  await page.evaluate((url) => { history.pushState({}, '', url); window.dispatchEvent(new PopStateEvent('popstate')); }, path);
}

test('a doctor switches clinics without seeing the other clinic and loses access after suspension', async ({ page, browser }) => {
  await login(page, 'e2e_tenant_doctor');
  await page.getByRole('button', { name: 'Clínica E2E A' }).click();
  await expect(page.getByRole('heading', { name: /Bienvenido/ })).toBeVisible();
  await navigateWithinApp(page, '/app/patients/list');
  await expect(page.getByText('SINTETICOA', { exact: false })).toBeVisible();
  await expect(page.getByText('SINTETICOB', { exact: false })).toHaveCount(0);
  const patientLink = page.getByRole('link', { name: 'Ver SINTETICOA' });
  const patientUrl = await patientLink.getAttribute('href');
  expect(patientUrl).toBeTruthy();
  await page.getByLabel('Clínica actual').selectOption({ label: 'Clínica E2E B' });
  await expect(page.getByRole('heading', { name: /Bienvenido/ })).toBeVisible();
  await navigateWithinApp(page, '/app/patients/list');
  await expect(page.getByText('SINTETICOB', { exact: false })).toBeVisible();
  await expect(page.getByText('SINTETICOA', { exact: false })).toHaveCount(0);
  await navigateWithinApp(page, patientUrl);
  await expect(page.getByText('SINTETICOA', { exact: false })).toHaveCount(0);
  await expect(page.getByRole('alert')).toBeVisible();

  const adminContext = await browser.newContext();
  const admin = await adminContext.newPage();
  try {
    await login(admin, 'e2e_tenant_admin');
    await admin.getByRole('button', { name: 'Clínica E2E B' }).click();
    const doctorRow = admin.getByRole('row').filter({ hasText: 'e2e_tenant_doctor' });
    await doctorRow.getByRole('button', { name: 'Suspender' }).click();
    await admin.getByRole('dialog').getByRole('button', { name: 'Confirmar cambio' }).click();
    await expect(doctorRow.getByRole('button', { name: 'Reactivar' })).toBeVisible();
    await navigateWithinApp(page, '/app/patients/list');
    await expect(page.getByText('SINTETICOB', { exact: false })).toHaveCount(0);
    await expect(page.getByRole('alert')).toBeVisible();
    await doctorRow.getByRole('button', { name: 'Revocar' }).click();
    await admin.getByRole('dialog').getByRole('button', { name: 'Confirmar cambio' }).click();
    await expect(doctorRow).toContainText('Requiere una nueva invitación');
  } finally {
    await adminContext.close();
  }
});

test('platform administrator onboards and activates a synthetic clinic', async ({ page }) => {
  await login(page, 'e2e_platform_admin');
  await page.getByRole('link', { name: 'Administración', exact: true }).click();
  await page.getByRole('link', { name: 'Clínicas', exact: true }).click();
  await page.getByLabel('Nombre', { exact: true }).fill('Clínica E2E Nueva');
  await page.getByLabel('Identificador').fill('clinica-e2e-nueva');
  await page.getByLabel('Correo del administrador inicial').fill('synthetic-admin@example.test');
  await page.getByRole('button', { name: 'Crear y enviar invitación' }).click();
  const clinicRow = page.getByRole('row').filter({ hasText: 'Clínica E2E Nueva' });
  await expect(clinicRow).toContainText('Inactiva');
  await clinicRow.getByRole('button', { name: 'Activar' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Confirmar cambio' }).click();
  await expect(clinicRow).toContainText('Activa');
  await clinicRow.getByRole('button', { name: 'Administración inicial' }).click();
  await expect(page.getByText('synthetic-admin@example.test')).toBeVisible();
});
