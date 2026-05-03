from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from mailbot.accounts import save_accounts_template, token_path_for
from mailbot.oauth_google import run_oauth_interactive
from mailbot.settings import settings

app = typer.Typer(no_args_is_help=True)


@app.command()
def init_config():
    """Write accounts.yaml template next to this project."""
    path = settings.accounts_path
    save_accounts_template(path)
    typer.echo(f"Wrote {path}. Edit it, add OAuth credentials.json, then: mailbot oauth <account_id>")


@app.command()
def oauth(account_id: str):
    """Run browser OAuth for one account id from accounts.yaml."""
    if not settings.credentials_path.is_file():
        typer.echo(
            f"Missing {settings.credentials_path}. Download OAuth client JSON from Google Cloud (Desktop).",
            err=True,
        )
        raise typer.Exit(1)
    token_path = token_path_for(account_id)
    typer.echo(
        "Ensure Google Cloud OAuth client 'Authorized redirect URIs' includes "
        f"http://127.0.0.1:{settings.oauth_redirect_port}/ "
        f"and http://localhost:{settings.oauth_redirect_port}/",
    )
    run_oauth_interactive(settings.credentials_path, token_path)
    typer.echo(f"Saved token to {token_path}")


@app.command()
def serve(
    host: str = typer.Option(settings.api_host, "--host"),
    port: int = typer.Option(settings.api_port, "--port"),
    reload: bool = typer.Option(False, "--reload"),
):
    """
    Run API on port 8765. Serves built UI from frontend/dist if present.
    For dev with HMR, run in another shell: cd frontend && npm run dev (proxies /api here).
    """
    uvicorn.run(
        "mailbot.api.main:app",
        host=host,
        port=port,
        reload=reload,
        factory=False,
    )


@app.command("gui")
def gui():
    """Alias for serve (opens backend + bundled SPA when frontend is built)."""
    uvicorn.run(
        "mailbot.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        factory=False,
    )


def main():
    app()


if __name__ == "__main__":
    main()
