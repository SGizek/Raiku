"""
raiku stats

Global ecosystem statistics from the package index.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore
from core.cache import CacheManager


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


@click.command("stats")
@click.pass_context
def stats_cmd(ctx: click.Context) -> None:
    """Show global Raiku ecosystem and local installation statistics."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # --- Index stats ---
    manager = IndexManager(index_url=cfg.index_url)
    try:
        index_stats = manager.stats()
        packages = manager.list_all()
    except IndexError:
        index_stats = None
        packages = []

    # --- Local cache stats ---
    cm = CacheManager(cfg.cache_dir)
    installed = cm.list_cached()
    cache_bytes = cm.total_size_bytes()

    # --- Top tags ---
    tag_counts: dict[str, int] = {}
    for pkg in packages:
        for tag in pkg.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]

    # --- Render ---
    console.print()

    # Index panel
    if index_stats:
        idx_table = Table(show_header=False, box=None, padding=(0, 2))
        idx_table.add_column("K", style="bold cyan")
        idx_table.add_column("V", style="white")
        idx_table.add_row("Total packages", str(index_stats["total"]))
        idx_table.add_row("Languages",      str(len(index_stats["by_language"])))
        if index_stats.get("synced_at"):
            import datetime
            dt = datetime.datetime.fromtimestamp(index_stats["synced_at"]).strftime("%Y-%m-%d %H:%M")
            idx_table.add_row("Index synced", dt)
        console.print(Panel(idx_table, title="[bold]Index[/bold]", border_style="cyan"))

        # Language breakdown
        lang_table = Table(show_header=True, header_style="bold magenta")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Packages", justify="right", style="green")
        lang_table.add_column("Bar", style="dim")
        max_count = max(index_stats["by_language"].values(), default=1)
        for lang, count in sorted(index_stats["by_language"].items(), key=lambda x: -x[1]):
            bar = "█" * int(count / max_count * 20)
            lang_table.add_row(lang, str(count), bar)
        console.print(lang_table)
    else:
        console.print("[yellow]No index loaded — run raiku sync.[/yellow]")

    # Local cache panel
    cache_table = Table(show_header=False, box=None, padding=(0, 2))
    cache_table.add_column("K", style="bold cyan")
    cache_table.add_column("V", style="white")
    cache_table.add_row("Installed packages", str(len(installed)))
    cache_table.add_row("Cache size",         _fmt_size(cache_bytes))
    cache_table.add_row("Cache directory",    str(cfg.cache_dir))
    console.print(Panel(cache_table, title="[bold]Local Cache[/bold]", border_style="green"))

    # Top tags
    if top_tags:
        tag_table = Table(show_header=True, header_style="bold magenta", title="Top Tags")
        tag_table.add_column("Tag",   style="cyan")
        tag_table.add_column("Count", justify="right", style="green")
        for tag, count in top_tags:
            tag_table.add_row(tag, str(count))
        console.print(tag_table)
