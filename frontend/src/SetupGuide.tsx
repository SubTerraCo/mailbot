import { useEffect, useState } from "react";
import { fetchOAuthHints, type AccountInfo, type OAuthHints } from "./api";

async function copyText(text: string, setHint: (s: string) => void) {
  try {
    await navigator.clipboard.writeText(text);
    setHint("Copied.");
    setTimeout(() => setHint(""), 2000);
  } catch {
    setHint("Select and copy manually.");
  }
}

function UriRow({ uri, onCopy }: { uri: string; onCopy: () => void }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6, flexWrap: "wrap" }}>
      <code style={{ fontSize: 12, wordBreak: "break-all", flex: 1, minWidth: 0 }}>{uri}</code>
      <button type="button" onClick={onCopy}>
        Copy
      </button>
    </div>
  );
}

export function SetupGuide({
  open,
  onClose,
  accounts,
}: {
  open: boolean;
  onClose: () => void;
  accounts: AccountInfo[];
}) {
  const [hints, setHints] = useState<OAuthHints | null>(null);
  const [copyHint, setCopyHint] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setErr(null);
    fetchOAuthHints()
      .then(setHints)
      .catch((e) => setErr(String(e)));
  }, [open]);

  if (!open) return null;

  return (
    <div className="setup-backdrop" role="dialog" aria-modal="true" aria-labelledby="setup-title">
      <div className="setup-panel">
        <div className="setup-header">
          <h2 id="setup-title">Connect Gmail (first-time setup)</h2>
          <button type="button" className="setup-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="setup-body">
          <p style={{ marginTop: 0, lineHeight: 1.5 }}>
            Mailbot needs a small <strong>credentials.json</strong> file from Google, then you click{" "}
            <strong>Connect in browser</strong> once per account listed in <code>accounts.yaml</code>.
          </p>

          <ol className="setup-steps">
            <li>
              <strong>Open Google Cloud</strong> →{" "}
              <a href="https://console.cloud.google.com/apis/library/gmail.googleapis.com" target="_blank" rel="noreferrer">
                enable Gmail API
              </a>
              , then{" "}
              <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer">
                Credentials
              </a>{" "}
              → create <strong>OAuth client ID</strong> (Desktop app is fine).
            </li>
            <li>
              <strong>Paste these “Authorized redirect URIs”</strong> into that OAuth client (exact match):
              {err && <div className="error" style={{ marginTop: 8 }}>{err}</div>}
              {hints && (
                <>
                  <p style={{ marginBottom: 6, fontSize: 13, color: "var(--muted)" }}>Browser sign-in (Mailbot):</p>
                  {hints.browserCallbackUris.map((u) => (
                    <UriRow key={u} uri={u} onCopy={() => void copyText(u, setCopyHint)} />
                  ))}
                  <p style={{ margin: "12px 0 6px", fontSize: 13, color: "var(--muted)" }}>CLI only (`mailbot oauth`):</p>
                  {hints.cliLoopbackUris.map((u) => (
                    <UriRow key={u} uri={u} onCopy={() => void copyText(u, setCopyHint)} />
                  ))}
                  {copyHint && <small style={{ color: "var(--ok)" }}>{copyHint}</small>}
                </>
              )}
            </li>
            <li>
              <strong>Download JSON</strong> from Google and save it as <code>credentials.json</code> next to{" "}
              <code>pyproject.toml</code>.
              {hints && (
                <div style={{ marginTop: 6, fontSize: 13 }}>
                  File detected:{" "}
                  <strong style={{ color: hints.credentialsPresent ? "var(--ok)" : "var(--danger)" }}>
                    {hints.credentialsPresent ? "yes" : "no"}
                  </strong>{" "}
                  <span style={{ color: "var(--muted)" }}>({hints.credentialsPath})</span>
                </div>
              )}
            </li>
            <li>
              <strong>OAuth consent screen</strong> → add every Gmail you use as a <strong>Test user</strong> while the
              app is in Testing mode.
            </li>
            <li>
              <strong>Connect each profile</strong> (opens Google in a new flow):
              <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 8 }}>
                {accounts.map((a) => (
                  <span key={a.id} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    <span className="pill">{a.id}</span>
                    {a.hasToken ? (
                      <span style={{ color: "var(--ok)", fontSize: 13 }}>already connected</span>
                    ) : (
                      <a className="button-link" href={`/api/oauth/google/start?account_id=${encodeURIComponent(a.id)}`}>
                        Connect {a.id}
                      </a>
                    )}
                  </span>
                ))}
              </div>
            </li>
          </ol>

          <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 0 }}>
            Longer walkthrough: see <code>docs/oauth-setup.md</code> in the repo. Dev UI tip: set{" "}
            <code>MAILBOT_OAUTH_SUCCESS_RETURN_URL</code> to your Vite URL if you use <code>npm run dev</code>.
          </p>
        </div>
        <div className="setup-footer">
          <button type="button" className="primary" onClick={onClose}>
            Back to Mailbot
          </button>
        </div>
      </div>
    </div>
  );
}
