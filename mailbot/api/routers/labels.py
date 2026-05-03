from __future__ import annotations

from fastapi import APIRouter

from mailbot.api.deps import get_gmail_service
from mailbot.gmail_ops import list_labels

router = APIRouter(prefix="/accounts", tags=["labels"])


@router.get("/{account_id}/labels")
def labels(account_id: str):
    svc = get_gmail_service(account_id)
    labs = list_labels(svc)
    return {"labels": labs}
