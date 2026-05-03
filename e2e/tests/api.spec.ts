import { expect, test, type APIRequestContext } from "@playwright/test";

async function postJson(request: APIRequestContext, path: string, body: unknown) {
  return request.post(path, {
    headers: { "Content-Type": "application/json" },
    data: JSON.stringify(body),
  });
}

test.beforeEach(async ({ request }) => {
  const res = await request.post("/api/e2e/reset");
  expect(res.ok()).toBeTruthy();
});

test("health", async ({ request }) => {
  const res = await request.get("/api/health");
  expect(res.ok()).toBeTruthy();
  expect(await res.json()).toEqual({ ok: true, e2e: true });
});

test("web OAuth start is disabled in E2E stub mode", async ({ request }) => {
  const res = await request.get("/api/oauth/google/start?account_id=personal", { maxRedirects: 0 });
  expect(res.status()).toBe(404);
});

test("oauth hints returns copy-paste redirect URIs and account ids", async ({ request }) => {
  const res = await request.get("/api/oauth/google/hints");
  expect(res.ok()).toBeTruthy();
  const j = await res.json();
  expect(j.browserCallbackUris.length).toBe(2);
  expect(j.cliLoopbackUris.length).toBe(2);
  expect(j.accountIds.sort()).toEqual(["personal", "work"]);
  expect(j.browserCallbackUris[0]).toContain("/api/oauth/google/callback");
});

test("accounts list marks tokens present in E2E", async ({ request }) => {
  const res = await request.get("/api/accounts");
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.accounts.map((a: { id: string }) => a.id).sort()).toEqual(["personal", "work"]);
  for (const a of body.accounts) {
    expect(a.hasToken).toBe(true);
  }
});

test("mixed index merges accounts and orders senders by latest activity", async ({ request }) => {
  const res = await request.get("/api/accounts/index/mixed");
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(new Set(body.accounts)).toEqual(new Set(["personal", "work"]));
  const addrs = body.senders.map((s: { address: string }) => s.address);
  expect(addrs).toContain("shop@store.example");
  expect(addrs).toContain("boss@corp.example");
  expect(addrs).toContain("alerts@corp.example");
  const shop = body.senders.find((s: { address: string }) => s.address === "shop@store.example");
  expect(shop.accountId).toBe("personal");
  expect(shop.messages[0].subject).toBe("Sale today");
});

test("per-account index builds full-address newest-first queue", async ({ request }) => {
  const res = await request.get("/api/accounts/personal/index");
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  const shop = body.senders.find((s: { address: string }) => s.address === "shop@store.example");
  expect(shop.count).toBe(3);
  expect(shop.messages.map((m: { subject: string }) => m.subject)).toEqual([
    "Sale today",
    "Newsletter",
    "Welcome",
  ]);
});

test("message modify adds labels and optional archive (no delete API)", async ({ request }) => {
  const res = await postJson(request, "/api/accounts/personal/messages/modify", {
    message_ids: ["p-new"],
    add_label_names: ["Mailbot/TestLabel"],
    remove_label_ids: [],
    archive: true,
  });
  expect(res.ok()).toBeTruthy();
  const msg = await request.get("/api/accounts/personal/messages/p-new");
  expect(msg.ok()).toBeTruthy();
  const m = await msg.json();
  expect(m.labelIds.length).toBeGreaterThanOrEqual(1);
  expect(m.labelIds).not.toContain("INBOX");
});

test("review-delete applies Mailbot/Review-Delete label", async ({ request }) => {
  const res = await postJson(request, "/api/accounts/personal/messages/review-delete", {
    message_ids: ["p-mid"],
    add_label_names: [],
    remove_label_ids: [],
    archive: false,
  });
  expect(res.ok()).toBeTruthy();
  const msg = await request.get("/api/accounts/personal/messages/p-mid");
  const m = await msg.json();
  expect(m.labelIds.some((id: string) => String(id).startsWith("Label_"))).toBeTruthy();
});

test("apply inbox rule with persist writes rules file", async ({ request }) => {
  const res = await postJson(request, "/api/accounts/personal/rules/apply-inbox", {
    match_type: "from_address",
    match_value: "shop@store.example",
    add_label_names: ["Mailbot/Newsletter"],
    archive: false,
    persist: true,
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.matched).toBe(3);
  const rules = await request.get("/api/rules");
  const rj = await rules.json();
  expect(rj.rules.length).toBe(1);
  expect(rj.rules[0].match.type).toBe("from_address");
  expect(rj.rules[0].match.value).toBe("shop@store.example");
});

test("rules delete removes persisted rule only", async ({ request }) => {
  await postJson(request, "/api/accounts/personal/rules/apply-inbox", {
    match_type: "from_domain",
    match_value: "corp.example",
    add_label_names: ["Mailbot/Corp"],
    archive: false,
    persist: true,
  });
  const list = await request.get("/api/rules");
  const { rules } = await list.json();
  expect(rules.length).toBeGreaterThanOrEqual(1);
  const id = rules[0].id as string;
  const del = await request.delete(`/api/rules/${id}`);
  expect(del.ok()).toBeTruthy();
  const after = await request.get("/api/rules");
  const body = await after.json();
  expect(body.rules.find((r: { id: string }) => r.id === id)).toBeUndefined();
});
