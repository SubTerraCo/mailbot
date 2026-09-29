# Gmail API auto sorting bot strategy

> **Chat export, not a spec.** Mailbot (`MB`) labels and archives. A later slice may read a bill PDF and hand line items to Billbot when both are installed. Google Sheets is not the system of record. Blueprint: `subterra-governance` `Docs/ARCHITECTURE.md`.
_Exported on 5/3/2026 at 03:14:04 MDT from Cursor (3.2.16)_

---

**User**

Can you help me a plan and execute a strategy to connect to Gmail's API to make an auto sorting bot? I want to pull out bills as well as itemize each bill into a spreadsheet. Namely I want to start with pulling all of my google fi bills out to a spreadsheet from the attached pdfs so I can bill each member on my fi plan. 

Let's take this step by step and work through this mail bot creation. Let's start planning! 

---

**Cursor**

Starting with a concrete plan. Checking the workspace for existing code we can build on.



The **Powerline** workspace looks empty, so we are planning greenfield. Here is a practical roadmap you can follow, then we can implement step by step in this repo when you are ready.

---

## Goal (narrow first slice)

1. **Find** Gmail messages that are Google Fi monthly bills (reliable filters: sender, subject, labels).
2. **Download** the bill PDF attachments.
3. **Extract** text (and ideally tables) from each PDF.
4. **Normalize** into rows (date, bill period, account line items, taxes, total, anything needed to split by member).
5. **Write** to a spreadsheet (Google Sheets is natural if you already live in Google).

Later you can generalize the same pipeline to “bills” broadly and add auto-labeling rules in Gmail.

---

## Architecture choices (pick once, then stay consistent)

| Piece | Option A | Option B |
|--------|-----------|-----------|
| Runtime | **Python** on your machine or a small VM | **Google Apps Script** (all inside Google) |
| Gmail | Gmail API (REST) | Same, or IMAP (worse for attachments at scale) |
| Auth | **OAuth desktop** or “installed app” flow, token stored locally | Service account **cannot** read a normal user’s Gmail without domain-wide delegation |
| PDF parsing | **pdfplumber** or **PyMuPDF** (good for text + rough tables) | Doc AI / custom parser if Fi layout breaks often |
| Sheets | **Sheets API** or `gspread` | Manual CSV import |

**Recommendation for your use case:** Python + Gmail API + pdfplumber (or PyMuPDF) + Google Sheets API (or CSV first, then import). It is the easiest path to iterate on Fi-specific parsing and keep secrets on your machine.

---

## Google Cloud / OAuth (required groundwork)

1. Create a **Google Cloud project**.
2. Enable **Gmail API** (and **Google Sheets API** if you want direct write).
3. Configure **OAuth consent screen** (External is fine for personal use; add yourself as test user while in “Testing”).
4. Create **OAuth client ID** → type **Desktop app** (or “Web” if you later host a small redirect).
5. Request **minimal scopes**, for example:
   - Read-only mail: `https://www.googleapis.com/auth/gmail.readonly`
   - If you need to move mail / add labels later: `gmail.modify` (add when you actually need it).
   - Sheets: `https://www.googleapis.com/auth/spreadsheets` only if the script creates/updates sheets.

Avoid `gmail` full access until you need it.

---

## Gmail strategy for Google Fi bills

You will tune this against your real inbox:

- **From:** often something like `@google.com` / Fi-specific noreply addresses (we will confirm from one real message).
- **Subject:** often contains “Your Google Fi bill” or similar (confirm from samples).
- **Query example (conceptual):** `from:(known-fi-sender) has:attachment filename:pdf subject:(bill OR Fi)`  
  Start broad, then tighten so you do not pull unrelated PDFs.

**Implementation steps in code:**

1. List messages with `users.messages.list` + `q=...`.
2. For each message, `users.messages.get` with `format=full` or `metadata` + attachment IDs.
3. For each `application/pdf` part, `users.messages.attachments.get` → base64 decode → save file with a stable name (`YYYY-MM_messageId.pdf`).

---

## PDF → spreadsheet (the hard part)

Fi PDFs are usually **visually structured** (not always clean tables). Plan in **two layers**:

1. **Extraction:** raw text per page + optional table candidates (pdfplumber’s `extract_tables()`).
2. **Fi-specific mapper:** regex / small rules for your bill version (they occasionally change layout).

**Deliverable shape for “bill each member”:** one sheet per bill **or** one long sheet with columns like:

- `bill_period_start`, `bill_period_end`
- `line_name` / `phone_number` (if shown)
- `plan_charge`, `data_usage_charge`, `device_payment`, `taxes_allocated`, `total_for_line`
- `source_pdf`, `gmail_message_id` (for audit)

You might not get perfect per-line taxes from the PDF; sometimes you **allocate** tax proportionally by subtotal. Document that assumption in the sheet.

**Phase 0 validation:** manually open 2–3 PDFs, note exactly which strings repeat (e.g. “Account charges”, “Member charges”), then encode those anchors in the parser.

---

## Execution strategy (phased, low risk)

1. **Phase 1 – Read-only discovery:** OAuth works; list 20 matching Fi messages; print IDs, dates, subjects, attachment filenames (no PDF parse yet).
2. **Phase 2 – Download:** save all Fi PDFs to a folder; verify count matches expectations.
3. **Phase 3 – Extract:** dump raw text to `.txt` per PDF; skim for stable patterns.
4. **Phase 4 – Parse v1:** map one bill end-to-end to a CSV row set; run on 3 historical bills and compare to PDF totals.
5. **Phase 5 – Sheets:** create/update a spreadsheet; optional Apps Script **only** if you want everything serverless later.
6. **Phase 6 – Bot behavior:** label + archive rules, dedupe by `messageId` or bill period, optional monthly cron.

---

## Risks and mitigations

- **OAuth token leakage:** keep `token.json` / secrets out of git (`.gitignore`); refresh token is sensitive.
- **Fragile PDF layout:** keep parser versioned; when Fi changes the PDF, adjust one module.
- **Wrong emails in query:** start with manual label in Gmail (`Fi-Bills`) and query `label:Fi-Bills` until filters are trusted.

---

## What I need from you next (to move from plan to build)

When you want to execute in this repo, the fastest path is:

1. One **example** (redacted is fine): typical **From** and **Subject** for a Fi bill email, or confirm you will use a dedicated **Gmail label** you apply manually.
2. Whether you prefer **Google Sheets** as the sink or **CSV** first.
3. Confirm **Python** on your machine is OK (version 3.10+).

Then we can implement Phase 1 in **Powerline**: project layout, `requirements.txt`, OAuth flow, and a script that only lists matching messages.

If you want this planning step to be more interactive (trade-offs, diagrams, or a formal checklist), say the word and we can switch to a dedicated planning thread; otherwise reply with the three bullets above and we will start **Phase 1** implementation in the next turn.

