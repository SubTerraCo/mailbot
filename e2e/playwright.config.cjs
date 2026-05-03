const path = require("path");
const { defineConfig, devices } = require("@playwright/test");

const repoRoot = path.join(__dirname, "..");
const accountsFixture = path.join(repoRoot, "tests", "fixtures", "accounts.e2e.yaml");
const rulesFixture = path.join(repoRoot, ".e2e", "rules.yaml");

module.exports = defineConfig({
  testDir: "./tests",
  // Single server + shared in-memory Gmail fake: avoid cross-test races
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  globalSetup: require.resolve("./global-setup.cjs"),
  use: {
    baseURL: "http://127.0.0.1:8799",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `python -m uvicorn mailbot.api.main:app --host 127.0.0.1 --port 8799`,
    cwd: repoRoot,
    env: {
      ...process.env,
      MAILBOT_E2E: "true",
      MAILBOT_ACCOUNTS_PATH: accountsFixture,
      MAILBOT_RULES_PATH: rulesFixture,
      MAILBOT_API_PORT: "8799",
      MAILBOT_INDEX_MAX_MESSAGES: "500",
    },
    // Must not reuse a dev server started without MAILBOT_E2E (would 401 modify routes).
    url: "http://127.0.0.1:8799/api/health",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
