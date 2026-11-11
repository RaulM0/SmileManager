import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, readdirSync, unlinkSync } from "node:fs";
import { join, resolve } from "node:path";
import process from "node:process";
import { setTimeout as delay } from "node:timers/promises";
import {
  startE2EServer,
  stopE2EServer,
} from "./server-lifecycle.js";

const root = resolve(import.meta.dirname, "../..");
const python = process.env.SMILE_E2E_PYTHON || resolve(
  root,
  process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python",
);
const manage = resolve(root, "manage.py");
export default async function globalSetup() {
  if (process.env.SMILE_E2E_EXTERNAL === '1') {
    process.env.SMILE_E2E_MAIL_DIR = process.env.SMILE_E2E_MAIL_DIR || join(root, '.e2e-browser-mail');
    for (const name of readdirSync(process.env.SMILE_E2E_MAIL_DIR)) {
      if (name.endsWith('.log')) unlinkSync(join(process.env.SMILE_E2E_MAIL_DIR, name));
    }
    for (let attempt = 0; attempt < 90; attempt += 1) {
      try {
        const response = await fetch('http://127.0.0.1:8010/health/ready/', { signal: AbortSignal.timeout(2000) });
        if (response.ok) return;
      } catch { /* El operador acaba de arrancar Django y todavía está cargando. */ }
      await delay(500);
    }
    throw new Error('El servicio E2E aislado no estuvo listo dentro del tiempo de espera.');
  }
  const directory = mkdtempSync(join(root, '.e2e-run-'));
  process.env.SMILE_E2E_MAIL_DIR = join(directory, 'mail');
  const env = { ...process.env, DJANGO_SETTINGS_MODULE: 'SmileManager.settings_e2e', SMILE_E2E_DIR: directory };
  let server;
  const cleanup = async () => {
    if (server) await stopE2EServer(server);
    // Windows may briefly retain the SQLite file after the server exits.
    // The directory is the fresh mkdtemp result under the project root.
    rmSync(directory, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
  };
  try {
  execFileSync(python, [manage, "migrate", "--noinput"], {
    cwd: root,
    env,
    stdio: "inherit",
  });
  execFileSync(python, [manage, "prepare_e2e"], {
    cwd: root,
    env,
    stdio: "inherit",
  });
    server = await startE2EServer(env);
    return cleanup;
  } catch (error) {
    await cleanup();
    throw error;
  }
}
