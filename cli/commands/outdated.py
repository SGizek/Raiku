"""
raiku outdated

Shows a clean report of installed packages that have newer versions
available in the index. Similar to pip list --outdated.
"""
from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table
from packaging.version import Version, InvalidVersion

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("outdated")
@click.option("--language", "-l", default=None, help="Filter by language.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def outdated_cmd(ctx: click.Context, language: str | None, as_json: bool) -> None:
    """Show installed packages that have newer versions available."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    manager = IndexManager(index_url=cfg.index_url)

    try:
        manager.load()
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]  Run [cyan]raiku sync[/cyan] first.")
        raise click.Abort()

    installed = store.list_installed()
    if language:
        installed = [p for p in installed if p.get("language", "").lower() == language.lower()]

    outdated: list[dict] = []
    up_to_date = 0

    for meta in installed:
        name = meta.get("name", "")
        current = meta.get("version", "0.0.0")
        entry = manager.find(name)
        if entry is None:
            continue
        latest = entry.get("version", "0.0.0")
        try:
            if Version(latest) > Version(current):
                outdated.append({
                    "name":     name,
                    "current":  current,
                    "latest":   latest,
                    "language": meta.get("language", "—"),
                })
            else:
                up_to_date += 1
        except InvalidVersion:
            up_to_date += 1

    if as_json:
        console.print(json.dumps(outdated, indent=2))
        return

    if not outdated:
        console.print(
            f"[bold green]✓ All {up_to_date} installed package(s) are up to date.[/bold green]"
        )
        return

    table = Table(
        title=f"Outdated Packages ({len(outdated)} of {len(installed)})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Package",   style="bold cyan")
    table.add_column("Installed", style="yellow")
    table.add_column("Latest",    style="green")
    table.add_column("Language",  style="dim")

    for pkg in sorted(outdated, key=lambda p: p["name"]):
        table.add_row(pkg["name"], pkg["current"], pkg["latest"], pkg["language"])

    console.print(table)
    console.print(
        f"\nRun [cyan]raiku update --all[/cyan] to update all, or "
        f"[cyan]raiku update <name>[/cyan] for a specific package."
    )
