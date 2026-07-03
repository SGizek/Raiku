"""
raiku sync

Fetches the latest index.json from the remote repository and
updates the local cache at ~/.raiku/index.json.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError


@click.command("sync")
@click.option(
    "--force", "-f", is_flag=True, default=False,
    help="Force sync even if the local index is fresh."
)
@click.pass_context
def sync_cmd(ctx: click.Context, force: bool) -> None:
    """Pull the latest package index from the Raiku repository."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    manager = IndexManager(index_url=cfg.index_url)

    if not force and not manager.is_stale():
        console.print(
            "[green]✓[/green] Local index is up-to-date. "
            "Use --force to sync anyway."
        )
        return

    console.print("[bold cyan]Raiku[/bold cyan] syncing package index...")

    try:
        data = manager.sync()
    except IndexError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort()

    stats = manager.stats()
    total = stats["total"]
    by_lang = stats["by_language"]

    console.print(f"[green]✓[/green] Index synced. "
                  f"[bold]{total}[/bold] packages available.\n")

    if cfg.verbose:
        table = Table(title="Packages by Language", show_header=True, header_style="bold magenta")
        table.add_column("Language", style="cyan")
        table.add_column("Packages", justify="right", style="green")
        for lang, count in sorted(by_lang.items()):
            table.add_row(lang, str(count))
        console.print(table)
