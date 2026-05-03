"""
Browser-based Google OAuth for Gmail (multi-account: one token per accounts.yaml id).

Requires credentials.json (Web or Desktop OAuth client). Register the exact
redirect URI (see resolved_oauth_redirect_uri()) in Google Cloud Console.
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from mailbot.accounts import load_accounts, token_path_for
from mailbot.oauth_google import SCOPES
from mailbot.oauth_state import consume_state, issue_state
from mailbot.settings import resolved_oauth_redirect_uri, resolved_oauth_success_return_url, settings

router = APIRouter(prefix="/oauth/google", tags=["oauth"])


@router.get("/hints")
def oauth_hints():
    """
    Exact strings to paste into Google Cloud Console (Authorized redirect URIs).
    """
    port = settings.api_port
    path = "/api/oauth/google/callback"
    web_uris = [
        f"http://127.0.0.1:{port}{path}",
        f"http://localhost:{port}{path}",
    ]
    cli_port = settings.oauth_redirect_port
    cli_uris = [
        f"http://127.0.0.1:{cli_port}/",
        f"http://localhost:{cli_port}/",
    ]
    ids = [a.id for a in load_accounts()]
    return {
        "credentialsPresent": settings.credentials_path.is_file(),
        "credentialsPath": str(settings.credentials_path),
        "apiPort": port,
        "accountIds": ids,
        "browserCallbackUris": web_uris,
        "cliLoopbackUris": cli_uris,
        "scopes": list(SCOPES),
        "successReturnUrlConfigured": bool(settings.oauth_success_return_url),
        "successReturnUrl": settings.oauth_success_return_url,
        "googleCloudConsole": "https://console.cloud.google.com/apis/credentials",
        "gmailApiEnable": "https://console.cloud.google.com/apis/library/gmail.googleapis.com",
    }


@router.get("/start")
def oauth_start(account_id: str = Query(..., description="accounts.yaml profile id")):
    if settings.e2e:
        raise HTTPException(status_code=404, detail="OAuth disabled in E2E mode")
    if not settings.credentials_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Missing OAuth client secrets: {settings.credentials_path}",
        )
    known = {a.id for a in load_accounts()}
    if account_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown account id: {account_id}")

    redirect_uri = resolved_oauth_redirect_uri()
    try:
        flow = Flow.from_client_secrets_file(
            str(settings.credentials_path),
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Invalid client secrets file: {e}") from e

    state = issue_state(account_id)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return RedirectResponse(url=authorization_url, status_code=302)


@router.get("/callback")
def oauth_callback(
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
):
    if settings.e2e:
        raise HTTPException(status_code=404, detail="OAuth disabled in E2E mode")

    base = resolved_oauth_success_return_url()

    def redirect_ui(params: dict[str, str]) -> RedirectResponse:
        return RedirectResponse(url=f"{base}/?{urlencode(params)}", status_code=302)

    if error:
        return redirect_ui({"oauth_error": error})
    if not code or not state:
        return redirect_ui({"oauth_error": "missing_code_or_state"})

    account_id = consume_state(state)
    if not account_id:
        return redirect_ui({"oauth_error": "invalid_or_expired_state"})

    redirect_uri = resolved_oauth_redirect_uri()
    try:
        flow = Flow.from_client_secrets_file(
            str(settings.credentials_path),
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
    except Exception as e:  # noqa: BLE001
        return redirect_ui({"oauth_error": str(e)[:500]})

    creds = flow.credentials
    token_path = token_path_for(account_id)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")

    return redirect_ui({"oauth_success": account_id})
