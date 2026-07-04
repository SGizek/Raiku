"""
raiku login    — store a GitHub Personal Access Token
raiku whoami   — show the currently authenticated user
raiku logout   — remove stored credentials

The token is stored at ~/.raiku/auth.json (chmod 600 on POSIX).
It is used by raiku publish --submit to open a PR automatically.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from core.config import RaikuConfig
from core.constants import RAIKU_HOME

AUTH_PATH = RAIKU_HOME / "auth.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_auth() -> dict:
    if AUTH_PATH.exists():
        try:
            return json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_auth(data: dict) -> None:
    AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Restrict permissions on POSIX so token is not world-readable
    try:
        os.chmod(AUTH_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass  # Windows — skip chmod


def get_token() -> str | None:
    return load_auth().get("token")


def get_username() -> str | None:
    return load_auth().get("username")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@click.command("login")
@click.option("--token", default=None,
              help="GitHub Personal Access Token. Prompted if not provided.")
@click.pass_context
def login_cmd(ctx: click.Context, token: str | None) -> None:
    """Store a GitHub Personal Access Token for raiku publish --submit."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if token is None:
        token = click.prompt("GitHub Personal Access Token", hide_input=True)

    if not token or len(token) < 10:
        console.print("[red]Invalid token.[/red]")
        raise click.exceptions.Exit(1)

    # Verify the token by calling GitHub API
    try:
        import requests
        resp = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=10,
        )
        if resp.status_code == 401:
            console.print("[red]Token is invalid or expired.[/red]")
            raise click.exceptions.Exit(1)
        resp.raise_for_status()
        user = resp.json()
        username = user.get("login", "unknown")
        name     = user.get("name", "")
    except Exception as exc:
        console.print(f"[yellow]Could not verify token: {exc}[/yellow]")
        console.print("[dim]Saving anyway — token may still work for publish.[/dim]")
        username = "unknown"
        name = ""

    save_auth({
        "token":    token,
        "username": username,
        "name":     name,
    })

    console.print(Panel(
        f"[green]✓ Logged in as[/green] [bold]{username}[/bold]"
        + (f" ({name})" if name else ""),
        border_style="green",
    ))
    console.print(f"  Token stored at [dim]{AUTH_PATH}[/dim]")
    console.print(
        "\n  Use [cyan]raiku publish --submit[/cyan] to open PRs automatically."
    )


@click.command("whoami")
@click.pass_context
def whoami_cmd(ctx: click.Context) -> None:
    """Show the currently authenticated GitHub user."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    auth = load_auth()
    if not auth or not auth.get("token"):
        console.print(
            "[yellow]Not logged in.[/yellow]  "
            "Run [cyan]raiku login[/cyan] to authenticate."
        )
        return

    console.print(
        f"[green]✓[/green] Logged in as [bold]{auth.get('username', 'unknown')}[/bold]"
        + (f" ({auth['name']})" if auth.get("name") else "")
    )
    console.print(f"  Auth file: [dim]{AUTH_PATH}[/dim]")


@click.command("logout")
@click.pass_context
def logout_cmd(ctx: click.Context) -> None:
    """Remove stored GitHub credentials."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if AUTH_PATH.exists():
        AUTH_PATH.unlink()
        console.print("[green]✓ Logged out.[/green] Credentials removed.")
    else:
        console.print("[dim]Not logged in.[/dim]")
