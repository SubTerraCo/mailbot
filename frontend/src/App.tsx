import { useCallback, useEffect, useMemo, useState } from "react";
import {
  applyRuleInbox,
  fetchAccounts,
  fetchLabels,
  fetchMixedIndex,
  modifyMessages,
  reviewDelete,
  type AccountInfo,
  type Msg,
  type SenderRow,
} from "./api";

function fmtDate(ms: number) {
  if (!ms) return "";
  return new Date(ms).toLocaleString();
}

export default function App() {
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [senders, setSenders] = useState<SenderRow[]>([]);
  const [filterAccount, setFilterAccount] = useState<string>("");
  const [selectedSender, setSelectedSender] = useState<SenderRow | null>(null);
  const [selectedMsg, setSelectedMsg] = useState<Msg | null>(null);
  const [labels, setLabels] = useState<{ id: string; name?: string }[]>([]);
  const [selectedLabelNames, setSelectedLabelNames] = useState<Set<string>>(new Set());
  const [newLabel, setNewLabel] = useState("");
  const [archive, setArchive] = useState(true);
  const [matchType, setMatchType] = useState<"from_address" | "from_domain">("from_address");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const loadAccounts = useCallback(async () => {
    const r = await fetchAccounts();
    setAccounts(r.accounts);
  }, []);

  const loadIndex = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetchMixedIndex();
      setSenders(r.senders);
      setStatus(`Indexed ${r.senders.length} sender groups (mixed accounts).`);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts().catch((e) => setError(String(e)));
  }, [loadAccounts]);

  useEffect(() => {
    loadIndex().catch((e) => setError(String(e)));
  }, [loadIndex]);

  const filteredSenders = useMemo(() => {
    if (!filterAccount) return senders;
    return senders.filter((s) => s.accountId === filterAccount);
  }, [senders, filterAccount]);

  const accountId = selectedSender?.accountId || "";

  useEffect(() => {
    if (!accountId) {
      setLabels([]);
      return;
    }
    fetchLabels(accountId)
      .then((r) => {
        const userLabs = (r.labels || []).filter((l) => l.type === "user");
        setLabels(userLabs.map((l) => ({ id: l.id, name: l.name || l.id })));
      })
      .catch((e) => setError(String(e)));
  }, [accountId]);

  const userLabelsByName = useMemo(() => {
    const m = new Map<string, string>();
    for (const l of labels) {
      if (l.name) m.set(l.name, l.id);
    }
    return m;
  }, [labels]);

  const toggleLabel = (name: string) => {
    setSelectedLabelNames((prev) => {
      const n = new Set(prev);
      if (n.has(name)) n.delete(name);
      else n.add(name);
      return n;
    });
  };

  const ensureExtraLabels = () => {
    const names = [...selectedLabelNames];
    if (newLabel.trim()) names.push(newLabel.trim());
    return names;
  };

  const matchValueForRule = () => {
    if (!selectedSender) return "";
    if (matchType === "from_address") return selectedSender.address;
    return selectedSender.domain || selectedSender.address.split("@")[1] || "";
  };

  const applyThis = async () => {
    if (!selectedMsg || !accountId) return;
    setError(null);
    try {
      await modifyMessages(accountId, {
        message_ids: [selectedMsg.id],
        add_label_names: ensureExtraLabels(),
        remove_label_ids: [],
        archive,
      });
      setStatus("Applied to current message.");
    } catch (e) {
      setError(String(e));
    }
  };

  const applyAllInbox = async () => {
    if (!accountId) return;
    const mv = matchValueForRule();
    if (!mv) return;
    setError(null);
    try {
      const r = (await applyRuleInbox(accountId, {
        match_type: matchType,
        match_value: mv,
        add_label_names: ensureExtraLabels(),
        archive,
        persist: false,
      })) as { matched?: number };
      setStatus(`Applied to ${r.matched ?? 0} messages in inbox matching rule (not saved).`);
    } catch (e) {
      setError(String(e));
    }
  };

  const saveFuture = async () => {
    if (!accountId) return;
    const mv = matchValueForRule();
    if (!mv) return;
    setError(null);
    try {
      const r = (await applyRuleInbox(accountId, {
        match_type: matchType,
        match_value: mv,
        add_label_names: ensureExtraLabels(),
        archive,
        persist: true,
      })) as { matched?: number };
      setStatus(`Applied to ${r.matched ?? 0} inbox messages and saved rule to data/rules.yaml.`);
    } catch (e) {
      setError(String(e));
    }
  };

  const junkReview = async () => {
    if (!selectedMsg || !accountId) return;
    setError(null);
    try {
      await reviewDelete(accountId, {
        message_ids: [selectedMsg.id],
        archive,
      });
      setStatus("Tagged Mailbot/Review-Delete (+ optional archive).");
    } catch (e) {
      setError(String(e));
    }
  };

  const msgList = selectedSender?.messages ?? [];
  const idx = selectedMsg ? msgList.findIndex((m) => m.id === selectedMsg.id) : -1;

  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      if (ev.target && (ev.target as HTMLElement).tagName === "INPUT") return;
      if (ev.target && (ev.target as HTMLElement).tagName === "TEXTAREA") return;
      if (ev.target && (ev.target as HTMLElement).tagName === "SELECT") return;
      if (!selectedSender || msgList.length === 0) return;
      if (ev.key === "j" || ev.key === "ArrowDown") {
        ev.preventDefault();
        const next = Math.min((idx < 0 ? 0 : idx) + 1, msgList.length - 1);
        setSelectedMsg(msgList[next]);
      }
      if (ev.key === "k" || ev.key === "ArrowUp") {
        ev.preventDefault();
        const next = Math.max((idx < 0 ? 0 : idx) - 1, 0);
        setSelectedMsg(msgList[next]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedSender, msgList, idx]);

  return (
    <div className="layout" data-testid="app-root">
      <section className="panel">
        <h2>Mail queue</h2>
        <div className="toolbar">
          <select
            data-testid="account-filter"
            value={filterAccount}
            onChange={(e) => setFilterAccount(e.target.value)}
          >
            <option value="">All accounts</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label} {!a.hasToken ? "(no token)" : ""}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="primary"
            data-testid="refresh-index"
            disabled={loading}
            onClick={() => loadIndex()}
          >
            Refresh index
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="hint">
          Shortcuts: <kbd>j</kbd>/<kbd>k</kbd> move in message list when a sender is selected.
        </div>
        <div className="scroll">
          {filteredSenders.map((s) => (
            <div
              key={`${s.accountId}:${s.address}`}
              data-testid="sender-row"
              data-account-id={s.accountId}
              data-address={s.address}
              className={`row ${selectedSender?.address === s.address && selectedSender?.accountId === s.accountId ? "active" : ""}`}
              onClick={() => {
                setSelectedSender(s);
                setSelectedMsg(s.messages[0] ?? null);
              }}
            >
              <div>
                <span className="pill">{s.accountId}</span> {s.address}
              </div>
              <small>
                {s.domain ? `${s.domain} · ` : ""}
                {s.count} msgs · latest {fmtDate(s.latestInternalDate)}
              </small>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Working message</h2>
        <div className="scroll">
          {selectedSender && (
            <>
              {msgList.map((m) => (
                <div
                  key={m.id}
                  data-testid="message-row"
                  data-message-id={m.id}
                  className={`row ${selectedMsg?.id === m.id ? "active" : ""}`}
                  onClick={() => setSelectedMsg(m)}
                >
                  <div style={{ fontWeight: 600 }}>{m.subject || "(no subject)"}</div>
                  <small>{fmtDate(m.internalDate)}</small>
                  <small>{m.snippet}</small>
                </div>
              ))}
              {selectedMsg && (
                <div className="msg-detail" data-testid="message-detail">
                  <h3 data-testid="message-detail-subject">{selectedMsg.subject || "(no subject)"}</h3>
                  <div className="pill">From {selectedSender.address}</div>
                  <div style={{ color: "var(--muted)", fontSize: 13 }}>{fmtDate(selectedMsg.internalDate)}</div>
                  <p style={{ lineHeight: 1.45 }}>{selectedMsg.snippet}</p>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      <section className="panel">
        <h2>Rule actions</h2>
        <div className="hint">
          Match scope for bulk / save:{" "}
          <select
            data-testid="match-type"
            value={matchType}
            onChange={(e) => setMatchType(e.target.value as "from_address" | "from_domain")}
          >
            <option value="from_address">Full address</option>
            <option value="from_domain">Domain</option>
          </select>
        </div>
        <div className="toolbar" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <button
            type="button"
            className="primary"
            data-testid="apply-this"
            disabled={!selectedMsg}
            onClick={() => void applyThis()}
          >
            Apply to this message
          </button>
          <button
            type="button"
            data-testid="apply-all-inbox"
            disabled={!selectedSender}
            onClick={() => void applyAllInbox()}
          >
            Apply all matching in inbox (now)
          </button>
          <button
            type="button"
            data-testid="save-future"
            disabled={!selectedSender}
            onClick={() => void saveFuture()}
          >
            Apply inbox + save rule for future
          </button>
          <button
            type="button"
            className="danger"
            data-testid="junk-review-delete"
            disabled={!selectedMsg}
            onClick={() => void junkReview()}
          >
            Junk: Review-Delete label
          </button>
        </div>
        {status && (
          <div className="hint" data-testid="status-line">
            {status}
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Labels & settings</h2>
        <div className="checkbox-line">
          <label>
            <input
              data-testid="archive-toggle"
              type="checkbox"
              checked={archive}
              onChange={(e) => setArchive(e.target.checked)}
            />
            Archive after apply (removes INBOX)
          </label>
        </div>
        <div className="toolbar" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <input
            data-testid="new-label-input"
            type="text"
            placeholder="New label name (e.g. Mailbot/Newsletter)"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
          />
        </div>
        <div className="label-grid">
          {labels
            .filter((l) => l.name)
            .sort((a, b) => (a.name || "").localeCompare(b.name || ""))
            .map((l) => (
              <label key={l.id}>
                <input
                  type="checkbox"
                  checked={selectedLabelNames.has(l.name!)}
                  onChange={() => toggleLabel(l.name!)}
                />
                <span>{l.name}</span>
              </label>
            ))}
        </div>
        <div className="hint">
          User label ids cached: {userLabelsByName.size}. Connect Gmail via <code>mailbot oauth &lt;id&gt;</code>.
        </div>
      </section>
    </div>
  );
}
