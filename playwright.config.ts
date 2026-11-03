import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60000,
  use: { headless: true, trace: "retain-on-failure" },
  workers: 1,
  reporter: "list",
});
