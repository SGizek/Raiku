"""
raiku list

Shows all packages currently installed in ~/.raiku/cache/.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from core.config import RaikuConfig
from installer.cache_store import CacheStore


@click.command("list")
@click.option(
    "--language", "-l", default=None,
    help="Filter by language.",
)
@click.option(
    "--json", "as_json", is_flag=True, default=False,
    help="Output as JSON.",
)
@click.pass_context
def list_cmd(ctx: click.Context, language: str | None, as_json: bool) -> None:
    """List all locally installed packages."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    packages = store.list_installed()

    if language:
        packages = [p for p in packages if p.get("language", "").lower() == language.lower()]

    if not packages:
        msg = "No packages installed"
        if language:
            msg += f" for language [cyan]{language}[/cyan]"
        console.print(f"[yellow]{msg}.[/yellow]")
        console.print("Run [cyan]raiku install <package>[/cyan] to install one.")
        return

    if as_json:
        import json
        console.print(json.dumps(packages, indent=2))
        return

    table = Table(
        title=f"Installed Packages{f' [{language}]' if language else ''}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Name", style="bold cyan", min_width=20)
    table.add_column("Version", style="green", min_width=8)
    table.add_column("Language", style="yellow", min_width=10)
    table.add_column("Author", style="white", min_width=15)
    table.add_column("Installed", style="dim", min_width=12)

    for pkg in sorted(packages, key=lambda p: p.get("name", "")):
        import datetime
        installed_at = pkg.get("installed_at")
        if installed_at:
            dt = datetime.datetime.fromtimestamp(installed_at).strftime("%Y-%m-%d")
        else:
            dt = "—"
        table.add_row(
            pkg.get("name", "—"),
            pkg.get("version", "—"),
            pkg.get("language", "—"),
            pkg.get("author", "—"),
            dt,
        )

    console.print(table)
    console.print(f"[dim]{len(packages)} package(s) installed.[/dim]")
