from fastapi import APIRouter, HTTPException

from mailbot.rules_store import save_rules
from mailbot.settings import settings
from mailbot.testing.fake_gmail import reset_fake_registry

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    return {"ok": True, "e2e": bool(settings.e2e)}


@router.post("/e2e/reset")
def e2e_reset():
    """Reset in-memory Gmail fakes and persisted rules (E2E only)."""
    if not settings.e2e:
        raise HTTPException(status_code=404, detail="Not available")
    reset_fake_registry()
    save_rules([])
    return {"ok": True}
