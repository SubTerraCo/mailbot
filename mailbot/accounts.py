from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from mailbot.settings import settings


class AccountEntry(BaseModel):
    id: str = Field(..., description="Stable profile id, e.g. personal")
    label: str | None = Field(None, description="Display name in UI")


def load_accounts(path: Path | None = None) -> list[AccountEntry]:
    p = path or settings.accounts_path
    if not p.is_file():
        return []
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    items = raw.get("accounts") or []
    out: list[AccountEntry] = []
    for row in items:
        if isinstance(row, dict):
            out.append(AccountEntry.model_validate(row))
        elif isinstance(row, str):
            out.append(AccountEntry(id=row))
    return out


def token_path_for(account_id: str) -> Path:
    settings.tokens_dir.mkdir(parents=True, exist_ok=True)
    return settings.tokens_dir / f"{account_id}.json"


def save_accounts_template(path: Path) -> None:
    sample: dict[str, Any] = {
        "accounts": [
            {"id": "personal", "label": "Personal Gmail"},
            {"id": "work", "label": "Work Gmail"},
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(sample, sort_keys=False), encoding="utf-8")
