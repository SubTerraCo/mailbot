"""
Gmail operations allowed by Mailbot (CRU-only).

Explicitly no: users.messages.delete, trash, batchDelete, drafts.delete.
"""

from __future__ import annotations

from typing import Any

from mailbot.parsing import extract_email_and_name, normalize_from_header


def _hdr(headers: list[dict[str, str]] | None, name: str) -> str | None:
    if not headers:
        return None
    name_l = name.lower()
    for h in headers:
        if (h.get("name") or "").lower() == name_l:
            return h.get("value")
    return None


def list_inbox_message_ids(service, query: str, max_total: int) -> list[str]:
    ids: list[str] = []
    page_token: str | None = None
    while len(ids) < max_total:
        remaining = max_total - len(ids)
        batch = min(500, remaining)
        req = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=batch, pageToken=page_token)
        )
        res = req.execute()
        for m in res.get("messages") or []:
            ids.append(m["id"])
            if len(ids) >= max_total:
                break
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return ids


def get_message_meta(service, msg_id: str) -> dict[str, Any]:
    return (
        service.users()
        .messages()
        .get(
            userId="me",
            id=msg_id,
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        )
        .execute()
    )


def extract_meta_fields(meta: dict[str, Any]) -> dict[str, Any]:
    payload = meta.get("payload") or {}
    headers = payload.get("headers") or []
    from_raw = _hdr(headers, "From")
    subject = _hdr(headers, "Subject") or ""
    email, display = extract_email_and_name(from_raw)
    full_from = normalize_from_header(from_raw) or email
    return {
        "id": meta.get("id"),
        "threadId": meta.get("threadId"),
        "internalDate": meta.get("internalDate"),
        "snippet": meta.get("snippet") or "",
        "labelIds": meta.get("labelIds") or [],
        "fromHeader": from_raw,
        "fromEmail": full_from,
        "fromDisplay": display,
        "subject": subject,
    }


def list_labels(service) -> list[dict[str, Any]]:
    res = service.users().labels().list(userId="me").execute()
    return list(res.get("labels") or [])


def ensure_label(service, name: str) -> str:
    """Return label id; create user label if missing."""
    labels = list_labels(service)
    for lab in labels:
        if lab.get("name") == name:
            return lab["id"]
    body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    created = service.users().labels().create(userId="me", body=body).execute()
    return created["id"]


def batch_modify(
    service,
    message_ids: list[str],
    add_label_ids: list[str] | None = None,
    remove_label_ids: list[str] | None = None,
) -> None:
    if not message_ids:
        return
    add_label_ids = add_label_ids or []
    remove_label_ids = remove_label_ids or []
    body: dict[str, Any] = {"ids": message_ids}
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids
    # Gmail batchModify limit 1000 ids per request
    chunk = 900
    for i in range(0, len(message_ids), chunk):
        chunk_ids = message_ids[i : i + chunk]
        b = dict(body)
        b["ids"] = chunk_ids
        service.users().messages().batchModify(userId="me", body=b).execute()


def get_user_profile_email(service) -> str | None:
    prof = service.users().getProfile(userId="me").execute()
    return prof.get("emailAddress")
