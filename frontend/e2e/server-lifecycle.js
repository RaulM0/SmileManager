import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { createServer } from "node:net";
import process from "node:process";

const root = resolve(import.meta.dirname, "../..");
const python = resolve(
  root,
  process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python",
);
const manage = resolve(root, "manage.py");
const serverUrl = "http://127.0.0.1:8010/app/login";

function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error.code === "ESRCH") return false;
    throw error;
  }
}

export async function startE2EServer(env) {
  // Never point the tests at an unrelated server that already owns the port.
  await new Promise((resolvePort, rejectPort) => {
    const probe = createServer();
    probe.once('error', rejectPort);
    probe.listen(8010, '127.0.0.1', () => probe.close((error) => error ? rejectPort(error) : resolvePort()));
  });
  const child = spawn(
    python,
    [manage, "runserver", "127.0.0.1:8010", "--noreload"],
    {
      cwd: root,
      env,
      stdio: "ignore",
      windowsHide: true,
    },
  );

  let launchError = null;
  let exitInfo = null;
  child.once("error", (error) => {
    launchError = error;
  });
  child.once("exit", (code, signal) => {
    exitInfo = { code, signal };
  });
  child.unref();

  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (launchError) throw launchError;
    if (exitInfo) {
      throw new Error(
        `El servidor E2E terminó al iniciar (código ${exitInfo.code}, señal ${exitInfo.signal}).`,
      );
    }
    try {
      const response = await fetch(serverUrl);
      if (response.ok) return child;
    } catch {
      // Django aún está iniciando o cargando el modelo clínico.
    }
    await delay(1000);
  }

  await stopE2EServer(child);
  throw new Error("El servidor E2E no respondió después de 120 segundos.");
}

export async function stopE2EServer(child) {
  const pid = child.pid;
  if (!Number.isInteger(pid) || !isProcessAlive(pid)) return;

  process.kill(pid, "SIGTERM");
  for (let attempt = 0; attempt < 50 && isProcessAlive(pid); attempt += 1) {
    await delay(100);
  }
  if (isProcessAlive(pid)) process.kill(pid, "SIGKILL");
}
