import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page, request }) => {
  const res = await request.post("/api/e2e/reset");
  expect(res.ok()).toBeTruthy();
  await page.goto("/");
  await expect(page.getByTestId("app-root")).toBeVisible();
});

test("Gmail setup help opens guided OAuth panel", async ({ page }) => {
  await page.getByTestId("open-setup").click();
  await expect(page.getByRole("heading", { name: "Connect Gmail (first-time setup)" })).toBeVisible();
  await expect(page.getByText("Browser sign-in (Mailbot):")).toBeVisible();
  await page.getByRole("button", { name: "Back to Mailbot" }).click();
  await expect(page.getByRole("heading", { name: "Connect Gmail (first-time setup)" })).not.toBeVisible();
});

test("four-column layout loads mixed sender queue", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Mail queue" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Working message" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Rule actions" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Labels & settings" })).toBeVisible();
  await expect(page.getByTestId("sender-row").filter({ hasText: "shop@store.example" })).toBeVisible();
  await expect(page.getByTestId("sender-row").filter({ hasText: "alerts@corp.example" })).toBeVisible();
});

test("select sender shows newest-first messages", async ({ page }) => {
  await page.getByTestId("sender-row").filter({ hasText: "shop@store.example" }).click();
  const first = page.locator('[data-testid="message-row"]').first();
  await expect(first).toContainText("Sale today");
  await expect(page.getByTestId("message-detail-subject")).toHaveText("Sale today");
});

test("j/k moves selection in message list", async ({ page }) => {
  await page.getByTestId("sender-row").filter({ hasText: "shop@store.example" }).click();
  await expect(page.getByTestId("message-detail-subject")).toHaveText("Sale today");
  await page.keyboard.press("j");
  await expect(page.getByTestId("message-detail-subject")).toHaveText("Newsletter");
  await page.keyboard.press("k");
  await expect(page.getByTestId("message-detail-subject")).toHaveText("Sale today");
});

test("account filter narrows sender rows", async ({ page }) => {
  await page.getByTestId("account-filter").selectOption("work");
  await expect(page.getByTestId("sender-row").filter({ hasText: "alerts@corp.example" })).toBeVisible();
  await expect(page.getByTestId("sender-row").filter({ hasText: "shop@store.example" })).toHaveCount(0);
});

test("junk review-delete shows success status", async ({ page }) => {
  await page.getByTestId("sender-row").filter({ hasText: "boss@corp.example" }).click();
  await page.getByTestId("junk-review-delete").click();
  await expect(page.getByTestId("status-line")).toContainText("Review-Delete");
});

test("save future rule shows status with saved wording", async ({ page }) => {
  await page.getByTestId("sender-row").filter({ hasText: "shop@store.example" }).click();
  await page.getByTestId("new-label-input").fill("Mailbot/E2E");
  await page.getByTestId("save-future").click();
  await expect(page.getByTestId("status-line")).toContainText("saved rule");
});
