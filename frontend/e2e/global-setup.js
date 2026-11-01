import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import process from "node:process";
import {
  startE2EServer,
  stopE2EServer,
} from "./server-lifecycle.js";

const root = resolve(import.meta.dirname, "../..");
const python = resolve(
  root,
  process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python",
);
const manage = resolve(root, "manage.py");
export default async function globalSetup() {
  const directory = mkdtempSync(join(root, '.e2e-run-'));
  const env = { ...process.env, DJANGO_SETTINGS_MODULE: 'SmileManager.settings_e2e', SMILE_E2E_DIR: directory };
  let server;
  const cleanup = async () => {
    if (server) await stopE2EServer(server);
    rmSync(directory, { recursive: true, force: true });
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
