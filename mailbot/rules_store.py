from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from mailbot.settings import settings


class RuleMatch(BaseModel):
    type: str = Field(..., description="from_address | from_domain")
    value: str


class RuleActions(BaseModel):
    add_labels: list[str] = Field(default_factory=list)
    archive: bool = False


class StoredRule(BaseModel):
    id: str
    account_id: str
    match: RuleMatch
    actions: RuleActions


def _ensure_rules_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(yaml.safe_dump({"rules": []}, sort_keys=False), encoding="utf-8")


def load_rules(path: Path | None = None) -> list[StoredRule]:
    p = path or settings.rules_path
    _ensure_rules_file(p)
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    rules = []
    for row in raw.get("rules") or []:
        rules.append(StoredRule.model_validate(row))
    return rules


def save_rules(rules: list[StoredRule], path: Path | None = None) -> None:
    p = path or settings.rules_path
    _ensure_rules_file(p)
    data = {"rules": [r.model_dump() for r in rules]}
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def gmail_query_for_rule(rule: StoredRule) -> str:
    m = rule.match
    if m.type == "from_address":
        return f"from:{m.value}"
    if m.type == "from_domain":
        return f"from:*@{m.value}"
    raise ValueError(f"Unknown match type {m.type}")
