from __future__ import annotations

from collections import defaultdict
from typing import Any

from mailbot.gmail_ops import extract_meta_fields, get_message_meta, list_inbox_message_ids
from mailbot.parsing import domain_from_email


def build_sender_index(service, inbox_query: str, max_messages: int) -> dict[str, Any]:
    """
    Group inbox messages by full From email; sort messages newest-first per sender.
    Sidebar order: senders by latest internalDate descending.
    """
    ids = list_inbox_message_ids(service, inbox_query, max_messages)
    by_sender: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for mid in ids:
        meta = get_message_meta(service, mid)
        fields = extract_meta_fields(meta)
        sender = fields.get("fromEmail")
        if not sender:
            sender = "(unknown)"
        internal_date = int(fields.get("internalDate") or 0)
        by_sender[sender].append(
            {
                "id": fields["id"],
                "threadId": fields.get("threadId"),
                "internalDate": internal_date,
                "snippet": fields.get("snippet") or "",
                "subject": fields.get("subject") or "",
                "fromHeader": fields.get("fromHeader"),
                "labelIds": fields.get("labelIds") or [],
            }
        )

    senders: list[dict[str, Any]] = []
    for addr, msgs in by_sender.items():
        msgs.sort(key=lambda m: m["internalDate"], reverse=True)
        latest = msgs[0]["internalDate"] if msgs else 0
        senders.append(
            {
                "address": addr,
                "domain": domain_from_email(addr if "@" in addr else None),
                "count": len(msgs),
                "latestInternalDate": latest,
                "messages": msgs,
            }
        )

    senders.sort(key=lambda s: s["latestInternalDate"], reverse=True)

    return {
        "senders": senders,
        "totalMessagesIndexed": len(ids),
        "truncated": len(ids) >= max_messages,
    }


def merge_sender_indexes(per_account: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge multiple accounts into one flat sender list with accountId on each row."""
    merged: list[dict[str, Any]] = []
    for account_id, idx in per_account.items():
        for s in idx.get("senders") or []:
            row = dict(s)
            row["accountId"] = account_id
            merged.append(row)
    merged.sort(key=lambda r: r.get("latestInternalDate") or 0, reverse=True)
    return merged
