from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from mailbot.settings import settings

# gmail.modify covers read + labels + archive (remove INBOX); avoid gmail.metadata-only if we need bodies later.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def creds_from_token_file(token_path: Path) -> Credentials | None:
    if not token_path.is_file():
        return None
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def run_oauth_interactive(credentials_json: Path, token_path: Path) -> Credentials:
    """
    Desktop OAuth: opens browser, saves refresh token to token_path.
    """
    credentials_json.parent.mkdir(parents=True, exist_ok=True)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_json), SCOPES)
    # Use fixed local port so GCP OAuth client can list http://127.0.0.1:PORT/
    creds = flow.run_local_server(
        port=settings.oauth_redirect_port,
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def get_or_refresh_creds(credentials_json: Path, token_path: Path) -> Credentials | None:
    creds = creds_from_token_file(token_path)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds
    return None
