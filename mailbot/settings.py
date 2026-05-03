from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAILBOT_", env_file=".env", extra="ignore")

    project_root: Path = Path(__file__).resolve().parent.parent
    credentials_path: Path = Path(__file__).resolve().parent.parent / "credentials.json"
    accounts_path: Path = Path(__file__).resolve().parent.parent / "accounts.yaml"
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    tokens_dir: Path = Path(__file__).resolve().parent.parent / "data" / "tokens"
    rules_path: Path = Path(__file__).resolve().parent.parent / "data" / "rules.yaml"

    api_host: str = "127.0.0.1"
    api_port: int = 8765

    # Gmail OAuth redirect for installed app
    oauth_redirect_port: int = 8766

    inbox_query: str = "in:inbox"
    index_max_messages: int = 2000

    # Playwright / CI: stub Gmail; no credentials.json required
    e2e: bool = False

    @field_validator("e2e", mode="before")
    @classmethod
    def _coerce_e2e(cls, v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "on")


settings = Settings()
