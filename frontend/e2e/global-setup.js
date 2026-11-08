import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import process from "node:process";
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
