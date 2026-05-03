from __future__ import annotations

from fastapi import APIRouter, HTTPException

from mailbot.rules_store import StoredRule, load_rules, save_rules

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules():
    return {"rules": [r.model_dump() for r in load_rules()]}


@router.delete("/{rule_id}")
def delete_rule(rule_id: str):
    """Remove persisted rule (does not touch Gmail)."""
    rules = load_rules()
    new_rules = [r for r in rules if r.id != rule_id]
    if len(new_rules) == len(rules):
        raise HTTPException(status_code=404, detail="Rule not found")
    save_rules(new_rules)
    return {"ok": True}
