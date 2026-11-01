import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.js",
  globalTeardown: "./e2e/global-teardown.js",
  fullyParallel: false,
  workers: 1,
  webServer: {
    command: ".venv/bin/python manage.py runserver 127.0.0.1:8010 --noreload",
    cwd: "..",
    env: { DJANGO_SETTINGS_MODULE: "SmileManager.settings_e2e" },
    url: "http://127.0.0.1:8010/app/login",
    reuseExistingServer: false,
    timeout: 120_000,
  },
  use: {
    baseURL:
      globalThis.process?.env.E2E_BASE_URL || "http://127.0.0.1:8010/app/",
    headless: true,
    browserName: "chromium",
    launchOptions: {
      executablePath:
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    },
  },
});
