// Predictable, single-use values are provisioned only by prepare_e2e under
// isolated E2E settings. The endpoints still enforce real MFA and replay checks.
const nextCodes = new Map();
function recoveryCode(username) {
  const index = nextCodes.get(username) || 0;
  nextCodes.set(username, index + 1);
  return `e2e-recovery-${username}-${index}`;
}

export async function completeMFA(page, username, password = 'e2e_password_123') {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const input = page.getByLabel('Código del autenticador o de recuperación');
    await input.waitFor({ state: 'visible' });
    await input.fill(recoveryCode(username));
    const [response] = await Promise.all([
      page.waitForResponse((result) => result.url().endsWith('/auth/mfa/verify/') && result.request().method() === 'POST'),
      page.getByRole('button', { name: 'Verificar', exact: true }).click(),
    ]);
    if (response.ok()) return;
    if ((attempt + 1) % 4 === 0) {
      await page.getByRole('button', { name: 'Volver al inicio de sesión' }).click();
      await page.getByLabel('Usuario', { exact: true }).fill(username);
      await page.getByLabel('Contraseña', { exact: true }).fill(password);
      await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
    }
  }
  throw new Error('No unused synthetic MFA recovery code was accepted');
}

export async function loginAPI(request, username, password = 'e2e_password_123') {
  let response = await request.post('/api/v1/auth/login/', { data: { username, password } });
  let result = await response.json();
  for (let attempt = 0; result.mfa_required && attempt < 20; attempt += 1) {
    response = await request.post('/api/v1/auth/mfa/verify/', { data: { challenge: result.challenge, code: recoveryCode(username) } });
    const verified = await response.json();
    if (response.ok()) return verified;
    if ((attempt + 1) % 4 === 0) result = await (await request.post('/api/v1/auth/login/', { data: { username, password } })).json();
  }
  if (!result.access) throw new Error('Synthetic API login failed');
  return result;
}
