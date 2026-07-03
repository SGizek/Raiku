"""
raiku pin / raiku unpin

Prevent (or allow) a package from being updated by raiku update --all.

    raiku pin fast-math              # pin at currently installed version
    raiku pin fast-math 1.0.0        # pin at specific version
    raiku unpin fast-math
    raiku pin --list
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
import datetime

from core.config import RaikuConfig
from core.pins import PinManager
from installer.cache_store import CacheStore


@click.group("pin")
@click.pass_context
def pin_cmd(ctx: click.Context) -> None:
    """Pin packages to prevent automatic updates."""
    pass


@pin_cmd.command("add")
@click.argument("package")
@click.argument("version", required=False, default=None)
@click.option("--reason", default="", help="Note explaining why this package is pinned.")
@click.pass_context
def pin_add(ctx: click.Context, package: str, version: str | None, reason: str) -> None:
    """Pin PACKAGE at VERSION (defaults to currently installed version)."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    pm = PinManager()

    if version is None:
        installed = store.list_installed()
        match = next((p for p in installed if p.get("name", "").lower() == package.lower()), None)
        if match is None:
            console.print(
                f"[red]'{package}' is not installed and no version specified.[/red]"
            )
            raise click.exceptions.Exit(1)
        version = match["version"]

    pm.pin(package, version, reason=reason)
    console.print(
        f"[green]✓[/green] Pinned [bold]{package}[/bold] at v{version}"
        + (f"  [dim]({reason})[/dim]" if reason else "")
    )


@pin_cmd.command("remove")
@click.argument("package")
@click.pass_context
def pin_remove(ctx: click.Context, package: str) -> None:
    """Remove pin from PACKAGE, allowing it to be updated again."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    pm = PinManager()
    if pm.unpin(package):
        console.print(f"[green]✓[/green] Unpinned [bold]{package}[/bold].")
    else:
        console.print(f"[yellow]'{package}' was not pinned.[/yellow]")


@pin_cmd.command("list")
@click.pass_context
def pin_list(ctx: click.Context) -> None:
    """Show all currently pinned packages."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    pm = PinManager()
    pins = pm.list_pins()

    if not pins:
        console.print("[dim]No packages are pinned.[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="bold cyan")
    table.add_column("Pinned Version", style="green")
    table.add_column("Pinned Since", style="dim")
    table.add_column("Reason", style="dim")

    for entry in sorted(pins, key=lambda e: e.get("name", "")):
        ts = entry.get("pinned_at")
        dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "—"
        table.add_row(
            entry.get("name", "—"),
            entry.get("version", "—"),
            dt,
            entry.get("reason", "—") or "—",
        )

    console.print(table)
    console.print(f"[dim]{len(pins)} pinned package(s).[/dim]")
