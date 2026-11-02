import { expect, test } from '@playwright/test';
import { Buffer } from 'node:buffer';

test('navegador y HTTP: sesión y aislamiento entre propietarios', async ({ page, request }) => {
  await page.goto('login');
  await page.getByLabel('Usuario').fill('e2e_doctor');
  await page.getByLabel('Contraseña', { exact: true }).fill('e2e_password_123');
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await expect(page.getByRole('heading', { name: /Bienvenido/ })).toBeVisible();
  const loginA = await request.post('/api/v1/auth/login/', { data: { username: 'e2e_doctor', password: 'e2e_password_123' } });
  expect(loginA.status()).toBe(200);
  const tokenA = (await loginA.json()).access;
  const created = await request.post('/api/v1/patients/', { headers: { Authorization: `Bearer ${tokenA}` }, data: {
    nombre: 'SINTETICO', appat: 'PRUEBA', apmat: 'E2E', fecha_nacimiento: '1990-01-01', genero: 'F', telefono: '1234567890', email: 'synthetic@example.test', estatus: 'A',
  } });
  expect(created.status()).toBe(201);
  const patientId = (await created.json()).id;
  const ownerHeaders = { Authorization: `Bearer ${tokenA}` };
  const consultation = await request.post(`/api/v1/patients/${patientId}/consultations/`, { headers: ownerHeaders, data: { motivo_consulta: 'control sintetico' } });
  expect(consultation.status()).toBe(201);
  const consultationId = (await consultation.json()).id;
  const appointment = await request.post('/api/v1/appointments/', { headers: ownerHeaders, data: { paciente_id: patientId, fecha: '2099-01-01', hora: '10:00', motivo: 'control', estatus: 'P' } });
  expect(appointment.status()).toBe(201);
  const appointmentId = (await appointment.json()).id;
  const image = await request.post(`/api/v1/patients/${patientId}/clinical-images/`, { headers: ownerHeaders, multipart: {
    consulta_id: String(consultationId), tipo_imagen: 'RX', descripcion: 'sintetica',
    imagen: { name: 'sintetica.png', mimeType: 'image/png', buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64') },
  } });
  expect(image.status()).toBe(201);
  const imageId = (await image.json()).id;
  const analysis = await request.post(`/api/v1/clinical-images/${imageId}/analyze/`, { headers: ownerHeaders, data: {} });
  expect(analysis.status()).toBe(200);
  const runId = (await analysis.json()).run_id;
  expect((await request.get(`/api/v1/clinical-images/${imageId}/analysis-runs/`, { headers: ownerHeaders })).status()).toBe(200);
  const retry = await request.post(`/api/v1/clinical-images/${imageId}/analyze/`, { headers: ownerHeaders, data: {} });
  expect((await retry.json()).run_id).toBe(runId);
  const forceHeaders = { ...ownerHeaders, 'Idempotency-Key': '11111111-1111-4111-8111-111111111111' };
  const forced = await request.post(`/api/v1/clinical-images/${imageId}/analyze/`, { headers: forceHeaders, data: { force: true } });
  expect(forced.status()).toBe(200);
  const forcedId = (await forced.json()).run_id;
  expect(forcedId).not.toBe(runId);
  const repeated = await request.post(`/api/v1/clinical-images/${imageId}/analyze/`, { headers: forceHeaders, data: { force: true } });
  expect((await repeated.json()).run_id).toBe(forcedId);
  const loginB = await request.post('/api/v1/auth/login/', { data: { username: 'e2e_other_doctor', password: 'e2e_password_123' } });
  expect(loginB.status()).toBe(200);
  const headers = { Authorization: `Bearer ${(await loginB.json()).access}` };
  for (const suffix of ['', 'medical-history/', 'odontogram/', 'consultations/', 'clinical-images/', 'consent/']) {
    const response = await request.get(`/api/v1/patients/${patientId}/${suffix}`, { headers });
    expect([403, 404], suffix).toContain(response.status());
  }
  for (const path of [`/api/v1/consultations/${consultationId}/`, `/api/v1/appointments/${appointmentId}/`, `/api/v1/clinical-images/${imageId}/`, `/api/v1/clinical-images/${imageId}/file/`, `/api/v1/clinical-images/${imageId}/analysis-runs/`, `/api/v1/clinical-images/${imageId}/analysis-runs/${runId}/file/`]) {
    expect([403, 404], path).toContain((await request.get(path, { headers })).status());
  }
  const storage = await page.evaluate(() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }));
  expect(storage.local.some((key) => /token|password/i.test(key))).toBeFalsy();
  expect(storage.session.some((key) => /token|password/i.test(key))).toBeFalsy();
  await page.goto('/app/design-system');
  await expect(page).toHaveURL(/\/app\/?$/);
  await expect(page.getByRole('heading', { name: /Bienvenido/ })).toBeVisible();
});
