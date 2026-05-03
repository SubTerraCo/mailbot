const apiBase = "";

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export type AccountInfo = { id: string; label: string; hasToken: boolean };

export async function fetchAccounts(): Promise<{ accounts: AccountInfo[] }> {
  return j("/api/accounts");
}

export type OAuthHints = {
  credentialsPresent: boolean;
  credentialsPath: string;
  apiPort: number;
  accountIds: string[];
  browserCallbackUris: string[];
  cliLoopbackUris: string[];
  scopes: string[];
  successReturnUrlConfigured: boolean;
  successReturnUrl: string | null;
  googleCloudConsole: string;
  gmailApiEnable: string;
};

export async function fetchOAuthHints(): Promise<OAuthHints> {
  return j("/api/oauth/google/hints");
}

export type SenderRow = {
  accountId: string;
  address: string;
  domain: string | null;
  count: number;
  latestInternalDate: number;
  messages: Msg[];
};

export type Msg = {
  id: string;
  threadId?: string;
  internalDate: number;
  snippet: string;
  subject: string;
};

export async function fetchMixedIndex(): Promise<{ senders: SenderRow[] }> {
  return j("/api/accounts/index/mixed");
}

export async function fetchAccountIndex(accountId: string) {
  return j(`/api/accounts/${accountId}/index`);
}

export type Label = { id: string; name?: string; type?: string };

export async function fetchLabels(accountId: string): Promise<{ labels: Label[] }> {
  return j(`/api/accounts/${accountId}/labels`);
}

export async function modifyMessages(
  accountId: string,
  body: {
    message_ids: string[];
    add_label_names: string[];
    remove_label_ids: string[];
    archive: boolean;
  },
) {
  return j(`/api/accounts/${accountId}/messages/modify`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function reviewDelete(
  accountId: string,
  body: {
    message_ids: string[];
    add_label_names?: string[];
    remove_label_ids?: string[];
    archive: boolean;
  },
) {
  return j(`/api/accounts/${accountId}/messages/review-delete`, {
    method: "POST",
    body: JSON.stringify({
      message_ids: body.message_ids,
      add_label_names: body.add_label_names ?? [],
      remove_label_ids: body.remove_label_ids ?? [],
      archive: body.archive,
    }),
  });
}

export async function applyRuleInbox(
  accountId: string,
  body: {
    match_type: "from_address" | "from_domain";
    match_value: string;
    add_label_names: string[];
    archive: boolean;
    persist: boolean;
  },
) {
  return j(`/api/accounts/${accountId}/rules/apply-inbox`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
