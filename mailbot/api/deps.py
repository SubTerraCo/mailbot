from __future__ import annotations

from fastapi import HTTPException

from mailbot.accounts import load_accounts, token_path_for
from mailbot.gmail_client import build_gmail_service
from mailbot.oauth_google import get_or_refresh_creds
from mailbot.settings import settings


def get_gmail_service(account_id: str):
    accounts = {a.id: a for a in load_accounts()}
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail=f"Unknown account id: {account_id}")
    creds = get_or_refresh_creds(settings.credentials_path, token_path_for(account_id))
    if not creds:
        raise HTTPException(
            status_code=401,
            detail=f"No valid token for '{account_id}'. Run: mailbot oauth {account_id}",
        )
    return build_gmail_service(creds)
