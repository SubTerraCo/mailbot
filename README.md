# Mailbot

Local Gmail sorting assistant (CRU-only: labels and archive, no delete/trash APIs). FastAPI backend + React (Vite) UI.

**“Deploy for free” locally** means: build the frontend once, run the Python server on your PC. No cloud bill; data stays on your machine.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for building the UI; optional if you only use a pre-built `frontend/dist`)
- Google Cloud project with **Gmail API** enabled and an **OAuth 2.0 Desktop** client → download `credentials.json` into the repo root.
- In the OAuth client, add **Authorized redirect URIs**:
  - `http://127.0.0.1:8766/`
  - `http://localhost:8766/`

## One-time setup

```bash
cd Mailbot
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
copy accounts.yaml.example accounts.yaml   # Windows: copy; edit IDs
# macOS/Linux: cp accounts.yaml.example accounts.yaml
```

Edit `accounts.yaml`, then for each account id:

```bash
mailbot oauth <account_id>
```

## Build (production-like local bundle)

```bash
pip install -e .
cd frontend
npm ci
npm run build
cd ..
```

This produces `frontend/dist/`. The Python app serves it when you run the server below.

## Run locally (free “deployment”)

```bash
mailbot serve
```

Open **http://127.0.0.1:8765** in your browser. API lives at **http://127.0.0.1:8765/api/**.

- **Host/port:** `MAILBOT_API_HOST`, `MAILBOT_API_PORT` (see `mailbot/settings.py`), or `mailbot serve --host 0.0.0.0 --port 8765` to listen on all interfaces (e.g. phone on same Wi‑Fi—use only on trusted networks).

`mailbot gui` is the same as `mailbot serve`.

## Development (hot reload UI)

Terminal A:

```bash
mailbot serve --reload
```

Terminal B:

```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173** (Vite proxies `/api` to port 8765).

## Optional: start on login (still free)

- **Windows:** Task Scheduler → trigger “At log on” → action “Start a program” → `pythonw` or full path to `mailbot.exe` / `uvicorn` with `mailbot.api.main:app`, start in repo directory.
- **macOS/Linux:** a small `systemd --user` service or `launchd` plist that runs `mailbot serve`.

Keep `credentials.json` and `data/tokens/` private; they are gitignored.

## Automated tests (Playwright)

End-to-end tests start a **stub Gmail** server (`MAILBOT_E2E=true`) so no real credentials are required.

```bash
cd e2e
npm install
npx playwright install chromium
npm test
```

The suite builds the frontend, starts Uvicorn on port **8799** with fixture accounts, hits the REST API, and drives the UI in Chromium. HTML report is written under `e2e/playwright-report/` (gitignored).

## Environment variables (optional)

| Variable | Purpose |
|----------|---------|
| `MAILBOT_CREDENTIALS_PATH` | Path to OAuth client JSON (default: `./credentials.json`) |
| `MAILBOT_ACCOUNTS_PATH` | Path to `accounts.yaml` |
| `MAILBOT_API_HOST` / `MAILBOT_API_PORT` | Bind address for `mailbot serve` |
| `MAILBOT_INDEX_MAX_MESSAGES` | Cap when scanning inbox (default 2000) |
| `MAILBOT_E2E` | `true` / `1` to enable in-memory Gmail stub (Playwright) |
| `MAILBOT_ACCOUNTS_PATH` | Override path to `accounts.yaml` |
| `MAILBOT_RULES_PATH` | Override path to persisted `rules.yaml` |

## License

Use at your own risk for personal mail automation; review Google API terms and your org’s policies.
