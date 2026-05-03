from __future__ import annotations

from fastapi import APIRouter

from mailbot.accounts import load_accounts, token_path_for
from mailbot.api.deps import get_gmail_service
from mailbot.gmail_ops import get_user_profile_email
from mailbot.indexing import build_sender_index, merge_sender_indexes
from mailbot.settings import settings

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
def list_accounts():
    out = []
    for a in load_accounts():
        tp = token_path_for(a.id)
        has_token = settings.e2e or tp.is_file()
        out.append(
            {
                "id": a.id,
                "label": a.label or a.id,
                "hasToken": has_token,
            }
        )
    return {"accounts": out}


@router.get("/{account_id}/profile")
def profile(account_id: str):
    svc = get_gmail_service(account_id)
    return {"email": get_user_profile_email(svc)}


@router.get("/{account_id}/index")
def sender_index(account_id: str):
    svc = get_gmail_service(account_id)
    data = build_sender_index(svc, settings.inbox_query, settings.index_max_messages)
    return {"accountId": account_id, **data}


@router.get("/index/mixed")
def mixed_index():
    per: dict[str, dict] = {}
    for a in load_accounts():
        if not settings.e2e and not token_path_for(a.id).is_file():
            continue
        svc = get_gmail_service(a.id)
        per[a.id] = build_sender_index(svc, settings.inbox_query, settings.index_max_messages)
    merged = merge_sender_indexes(per)
    return {
        "accounts": list(per.keys()),
        "senders": merged,
        "perAccountMeta": {k: {"totalMessagesIndexed": v["totalMessagesIndexed"], "truncated": v["truncated"]} for k, v in per.items()},
    }
