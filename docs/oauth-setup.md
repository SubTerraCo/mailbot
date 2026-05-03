# Gmail OAuth for Mailbot (simple steps)

You are telling Google: “This Mailbot app on my computer may read and change my Gmail labels (not delete mail).” You do that once per Google Cloud project, then sign in once per Mailbot account.

---

## Part A — Google website (one time per project)

### 1) Open Google Cloud

Go to: **[Google Cloud Console](https://console.cloud.google.com/)**  
Sign in with the Google account you use for Cloud (can be any Google account).

### 2) Create or pick a project

Top bar → project dropdown → **New project** (or pick an existing one).  
Give it any name (e.g. `Mailbot`).

### 3) Turn on the Gmail API

1. Left menu: **APIs & Services** → **Library**  
2. Search **Gmail API** → **Enable**

### 4) Configure the “OAuth consent screen”

1. **APIs & Services** → **OAuth consent screen**  
2. User type: **External** (fine for personal use) → Create  
3. Fill **App name** (e.g. `Mailbot`), your email, then save through the steps  
4. Under **Test users**: add **each Gmail address** you will connect (important while the app is in “Testing”).

### 5) Create OAuth “Client ID” credentials

1. **APIs & Services** → **Credentials**  
2. **+ Create credentials** → **OAuth client ID**  
3. Application type: **Desktop app** (easiest) — *or* **Web application** if you prefer  
4. Name: anything (e.g. `Mailbot desktop`)

### 6) Add redirect addresses (copy-paste)

Still on that credential, find **Authorized redirect URIs** and click **Add URI** for **each** line below (or use the **Setup** panel in Mailbot — it reads your real port and has Copy buttons).

**For sign-in inside Mailbot’s browser flow** (API on port **8765** by default):

- `http://127.0.0.1:8765/api/oauth/google/callback`
- `http://localhost:8765/api/oauth/google/callback`

**For the command line** `mailbot oauth` (separate small server on port **8766**):

- `http://127.0.0.1:8766/`
- `http://localhost:8766/`

If you changed the API port (`MAILBOT_API_PORT`), replace **8765** in the first two lines with your port.

### 7) Download the JSON file

On the credential you just created → **Download JSON**  
Rename/move it to your Mailbot folder as **`credentials.json`** (same folder as `pyproject.toml`).

---

## Part B — Mailbot on your computer

### 8) List your Gmail profiles

Edit **`accounts.yaml`**: each block is one saved login (id + label). Example:

```yaml
accounts:
  - id: personal
    label: Personal Gmail
  - id: work
    label: Work Gmail
```

### 9) Sign in to each Gmail

1. Run `mailbot serve` and open **http://127.0.0.1:8765**  
2. Optional: open **http://127.0.0.1:8765/?setup=1** for the guided panel with copy buttons  
3. Under **Gmail sign-in**, click **Connect in browser** for each account and approve in Google.

Tokens are stored under **`data/tokens/<id>.json`**. You can repeat step 3 for every id in `accounts.yaml`.

---

## If something fails

| Symptom | What to check |
|--------|----------------|
| `redirect_uri_mismatch` | Redirect URIs in Google must match **exactly** (including `http`, port, and path). Use Mailbot’s **Setup** panel to copy the lines. |
| `Access blocked` / test users | Add that Gmail address under OAuth consent screen **Test users**. |
| `Missing OAuth client secrets` | `credentials.json` is missing or not next to `pyproject.toml`. |
| After login you don’t return to the app | If you use Vite on port 5173, set `MAILBOT_OAUTH_SUCCESS_RETURN_URL=http://127.0.0.1:5173` when starting the API. |

---

That’s it: **Google Cloud once**, **`credentials.json` once**, then **Connect in browser** per account in Mailbot.
