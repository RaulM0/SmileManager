import { expect, test } from '@playwright/test';
import { completeMFA } from './mfa-helper.js';
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import process from 'node:process';

async function recoveryLink(email, excluded = '') {
  const directory = process.env.SMILE_E2E_MAIL_DIR;
  if (!directory) throw new Error('Falta el directorio aislado de correo E2E.');
  let result = '';
  await expect.poll(async () => {
    let files;
    try { files = await readdir(directory); } catch { return false; }
    for (const file of files) {
      const message = (await readFile(join(directory, file), 'utf8')).replace(/=\r?\n/g, '').replace(/=3D/gi, '=');
      if (!message.includes(email)) continue;
      const match = message.match(/http:\/\/127\.0\.0\.1:8010\/app\/reset-password#uid=[A-Za-z0-9_-]+&token=[A-Za-z0-9-]+/);
      if (match && match[0] !== excluded) { result = match[0]; return true; }
    }
    return false;
  }, { timeout: 15000 }).toBe(true);
  return result;
}

for (const username of ['e2e_doctor', 'e2e_system_admin']) {
  test(`recuperación de ${username}`, async ({ page }) => {
    const email = `${username}@example.test`;
    await page.goto('login');
    await page.getByRole('link', { name: '¿Olvidaste tu contraseña?' }).click();
    await page.getByLabel('Correo electrónico').fill(email);
    await page.getByRole('button', { name: 'Enviar instrucciones' }).click();
    await expect(page.getByText(/Si existe una cuenta elegible/)).toBeVisible();
    const link = await recoveryLink(email);
    const secret = new URLSearchParams(new URL(link).hash.slice(1)).get('token');
    expect(Boolean(secret)).toBe(true);
    await page.goto(link);
    await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('');
    const stored = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }));
    expect(stored.includes(secret)).toBe(false);
    await page.getByLabel('Nueva contraseña').fill('Nuevas credenciales seguras 459!');
    await page.getByLabel('Confirmar contraseña').fill('Nuevas credenciales seguras 459!');
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click();
    await expect(page.getByText('Tu contraseña se actualizó correctamente.')).toBeVisible();
    await page.getByRole('link', { name: 'Iniciar sesión' }).click();
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Contraseña', { exact: true }).fill('e2e_password_123');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page.getByText('Usuario o contraseña incorrectos')).toBeVisible();
    await page.getByLabel('Contraseña', { exact: true }).fill('Nuevas credenciales seguras 459!');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    if (username === 'e2e_system_admin') await completeMFA(page, username, 'Nuevas credenciales seguras 459!');
    await expect(page.getByRole('heading', { name: /Bienvenido/ })).toBeVisible();
    if (username === 'e2e_system_admin') await expect(page.getByRole('link', { name: 'Administración', exact: true })).toBeVisible();
    // Restore the shared synthetic account through the same public contract so
    // later specs do not depend on whether recovery ran before or after them.
    expect((await page.request.post('/api/v1/auth/password-reset/request/', { data: { email } })).status()).toBe(200);
    const restoreLink = await recoveryLink(email, link);
    const values = new URLSearchParams(new URL(restoreLink).hash.slice(1));
    const restored = await page.request.post('/api/v1/auth/password-reset/confirm/', { data: {
      uid: values.get('uid'), token: values.get('token'),
      new_password: 'e2e_password_123', confirm_password: 'e2e_password_123',
    } });
    expect(restored.status()).toBe(200);
  });
}
