import { defineConfig } from "@playwright/test";
import process from "node:process";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.js",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8010/app/",
    headless: true,
    browserName: "chromium",
    launchOptions: process.env.SMILE_E2E_BROWSER ? { executablePath: process.env.SMILE_E2E_BROWSER } : {},
  },
});
