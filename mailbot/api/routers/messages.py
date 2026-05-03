from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mailbot.api.deps import get_gmail_service
from mailbot.constants import REVIEW_DELETE_LABEL
from mailbot.gmail_ops import batch_modify, ensure_label, get_message_meta, list_inbox_message_ids
from mailbot.gmail_ops import extract_meta_fields as extract_fields
from mailbot.rules_store import RuleActions, RuleMatch, StoredRule, gmail_query_for_rule, load_rules, save_rules
from mailbot.settings import settings

router = APIRouter(prefix="/accounts", tags=["messages"])


class ModifyBody(BaseModel):
    message_ids: list[str]
    add_label_names: list[str] = Field(default_factory=list)
    remove_label_ids: list[str] = Field(default_factory=list)
    archive: bool = False


# Static /messages/* paths MUST be declared before /messages/{message_id} or "modify" is captured as an id.


@router.post("/{account_id}/messages/modify")
def modify_messages(account_id: str, body: ModifyBody):
    svc = get_gmail_service(account_id)
    add_ids: list[str] = []
    for name in body.add_label_names:
        add_ids.append(ensure_label(svc, name))
    remove_ids = list(body.remove_label_ids)
    if body.archive:
        remove_ids.append("INBOX")
    remove_ids = list(dict.fromkeys(remove_ids))
    batch_modify(svc, body.message_ids, add_label_ids=add_ids, remove_label_ids=remove_ids or None)
    return {"ok": True, "modified": len(body.message_ids)}


@router.post("/{account_id}/messages/review-delete")
def review_delete(account_id: str, body: ModifyBody):
    """Convenience: add junk-review label + optional archive."""
    body = body.model_copy(
        update={
            "add_label_names": list(dict.fromkeys([*body.add_label_names, REVIEW_DELETE_LABEL])),
        }
    )
    return modify_messages(account_id, body)


@router.get("/{account_id}/messages/{message_id}")
def one_message(account_id: str, message_id: str):
    svc = get_gmail_service(account_id)
    meta = get_message_meta(svc, message_id)
    return extract_fields(meta)


class ApplyRuleDraft(BaseModel):
    """Apply rule to inbox now + optionally persist."""

    match_type: str = Field(..., description="from_address | from_domain")
    match_value: str
    add_label_names: list[str] = Field(default_factory=list)
    archive: bool = False
    persist: bool = False


@router.post("/{account_id}/rules/apply-inbox")
def apply_rule_to_inbox(account_id: str, draft: ApplyRuleDraft):
    svc = get_gmail_service(account_id)
    rule = StoredRule(
        id=str(uuid.uuid4()),
        account_id=account_id,
        match=RuleMatch(type=draft.match_type, value=draft.match_value),
        actions=RuleActions(add_labels=draft.add_label_names, archive=draft.archive),
    )
    q = f"in:inbox {gmail_query_for_rule(rule)}"
    ids = list_inbox_message_ids(svc, q, settings.index_max_messages)
    add_ids = [ensure_label(svc, n) for n in draft.add_label_names]
    remove = ["INBOX"] if draft.archive else []
    batch_modify(svc, ids, add_label_ids=add_ids, remove_label_ids=remove or None)

    saved: dict[str, Any] | None = None
    if draft.persist:
        rules = load_rules()
        rules.append(rule)
        save_rules(rules)
        saved = rule.model_dump()

    return {"ok": True, "matched": len(ids), "query": q, "savedRule": saved}
