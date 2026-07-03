"""
raiku cache

Cache management commands:
  raiku cache --info    Show disk usage and installed package count
  raiku cache --clear   Wipe the entire cache (with confirmation)
"""
from __future__ import annotations

import shutil

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from core.config import RaikuConfig
from core.cache import CacheManager


def _fmt_size(n: int) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


@click.command("cache")
@click.option("--info", "show_info", is_flag=True, default=False,
              help="Show cache statistics.")
@click.option("--clear", "do_clear", is_flag=True, default=False,
              help="Wipe the entire package cache.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt for --clear.")
@click.pass_context
def cache_cmd(
    ctx: click.Context,
    show_info: bool,
    do_clear: bool,
    yes: bool,
) -> None:
    """Manage the local package cache."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if not show_info and not do_clear:
        console.print(
            "Specify an action:\n"
            "  [cyan]raiku cache --info[/cyan]    — show cache statistics\n"
            "  [cyan]raiku cache --clear[/cyan]   — wipe the entire cache"
        )
        return

    manager = CacheManager(cfg.cache_dir)

    if show_info:
        _show_info(console, manager, cfg)

    if do_clear:
        _do_clear(console, manager, cfg, yes)


def _show_info(console: Console, manager: CacheManager, cfg: RaikuConfig) -> None:
    packages = manager.list_cached()
    total_bytes = manager.total_size_bytes()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")
    table.add_row("Cache directory", str(cfg.cache_dir))
    table.add_row("Installed packages", str(len(packages)))
    table.add_row("Total disk usage", _fmt_size(total_bytes))

    console.print(Panel(table, title="Cache Info"))

    if packages and cfg.verbose:
        pkg_table = Table(show_header=True, header_style="bold magenta")
        pkg_table.add_column("Name", style="bold cyan")
        pkg_table.add_column("Version", style="green")
        pkg_table.add_column("Language", style="yellow")
        for p in sorted(packages, key=lambda x: x.get("name", "")):
            pkg_table.add_row(
                p.get("name", "—"),
                p.get("version", "—"),
                p.get("language", "—"),
            )
        console.print(pkg_table)


def _do_clear(
    console: Console,
    manager: CacheManager,
    cfg: RaikuConfig,
    yes: bool,
) -> None:
    packages = manager.list_cached()
    total_bytes = manager.total_size_bytes()

    if not cfg.cache_dir.exists() or not packages:
        console.print("[yellow]Cache is already empty.[/yellow]")
        return

    console.print(
        f"  This will remove [bold]{len(packages)}[/bold] package(s) "
        f"({_fmt_size(total_bytes)}) from [dim]{cfg.cache_dir}[/dim]"
    )

    if not yes:
        confirmed = Confirm.ask("Wipe the entire cache?", default=False)
        if not confirmed:
            console.print("[dim]Aborted.[/dim]")
            return

    shutil.rmtree(cfg.cache_dir, ignore_errors=True)
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    console.print("[bold green]✓ Cache cleared.[/bold green]")
