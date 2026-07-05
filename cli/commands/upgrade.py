"""
raiku upgrade

Upgrades the Raiku CLI itself to the latest version from GitHub.
Compares the current installed version against the latest tag on GitHub,
then runs pip install to upgrade in-place.
"""
from __future__ import annotations

import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from packaging.version import Version

from core.config import RaikuConfig
from core.constants import VERSION, REPO_OWNER, REPO_NAME


@click.command("upgrade")
@click.option("--check", is_flag=True, default=False,
              help="Only check for a newer version, do not install.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt.")
@click.pass_context
def upgrade_cmd(ctx: click.Context, check: bool, yes: bool) -> None:
    """Upgrade the Raiku CLI to the latest version from GitHub."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("[bold cyan]Raiku Upgrade[/bold cyan] — checking for new version...\n")

    latest = _fetch_latest_version(console)
    if latest is None:
        raise click.exceptions.Exit(1)

    current = VERSION
    console.print(f"  Installed : [yellow]{current}[/yellow]")
    console.print(f"  Latest    : [green]{latest}[/green]")

    try:
        is_newer = Version(latest) > Version(current)
    except Exception:
        is_newer = latest != current

    if not is_newer:
        console.print(
            f"\n[bold green]✓ Raiku is already up to date (v{current}).[/bold green]"
        )
        return

    if check:
        console.print(
            f"\n[yellow]Update available:[/yellow] v{current} → v{latest}\n"
            "Run [cyan]raiku upgrade[/cyan] to install."
        )
        return

    if not yes:
        from rich.prompt import Confirm
        if not Confirm.ask(f"\nUpgrade Raiku v{current} → v{latest}?", default=True):
            console.print("[dim]Aborted.[/dim]")
            return

    console.print(f"\n  Upgrading v{current} → v{latest}...")
    pip_target = f"git+https://github.com/{REPO_OWNER}/{REPO_NAME}.git@v{latest}"

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", pip_target],
        capture_output=False,
    )

    if result.returncode == 0:
        console.print(Panel(
            f"[bold green]✓ Raiku upgraded to v{latest}[/bold green]\n\n"
            "Restart your shell or run [cyan]raiku --version[/cyan] to confirm.",
            border_style="green",
        ))
    else:
        console.print(
            f"[red]Upgrade failed (exit {result.returncode}).[/red]\n"
            f"Try manually: pip install --upgrade {pip_target}"
        )
        raise click.exceptions.Exit(result.returncode)


def _fetch_latest_version(console: Console) -> str | None:
    """Return the latest release tag from GitHub, or None on failure."""
    try:
        import requests
        resp = requests.get(
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if resp.status_code == 404:
            # No releases yet — fall back to tags
            tags_resp = requests.get(
                f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/tags",
                timeout=10,
            )
            if tags_resp.ok:
                tags = tags_resp.json()
                if tags:
                    return tags[0]["name"].lstrip("v")
            console.print("[yellow]No releases found on GitHub.[/yellow]")
            return None
        resp.raise_for_status()
        tag = resp.json().get("tag_name", "").lstrip("v")
        return tag or None
    except Exception as exc:
        console.print(f"[red]Could not fetch latest version: {exc}[/red]")
        return None
