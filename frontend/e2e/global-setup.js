import { execFileSync } from "node:child_process";
import { rmSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const database = resolve(root, ".e2e.sqlite3");
const media = resolve(root, ".e2e-media");
const python = resolve(root, ".venv/bin/python");
const manage = resolve(root, "manage.py");
const env = {
  ...globalThis.process.env,
  DJANGO_SETTINGS_MODULE: "SmileManager.settings_e2e",
};

export default function globalSetup() {
  rmSync(database, { force: true });
  rmSync(media, { recursive: true, force: true });
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
}
