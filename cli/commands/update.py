"""
raiku update [package]

Checks for newer versions of installed packages and reinstalls them.

    raiku update fast-math      # update one package
    raiku update --all          # update every installed package
"""
from __future__ import annotations

from packaging.version import Version, InvalidVersion

import click
from rich.console import Console
from rich.table import Table

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("update")
@click.argument("package", required=False, default=None)
@click.option(
    "--all", "update_all", is_flag=True, default=False,
    help="Update every installed package.",
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Show what would be updated without installing.",
)
@click.pass_context
def update_cmd(
    ctx: click.Context,
    package: str | None,
    update_all: bool,
    dry_run: bool,
) -> None:
    """Check for updates and reinstall newer versions."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if not package and not update_all:
        console.print(
            "[yellow]Specify a package name or use --all.[/yellow]\n"
            "  raiku update fast-math\n"
            "  raiku update --all"
        )
        raise click.exceptions.Exit(1)

    store = CacheStore(cfg.cache_dir)
    manager = IndexManager(index_url=cfg.index_url)

    try:
        manager.load()
    except IndexError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        console.print("Run [cyan]raiku sync[/cyan] first.")
        raise click.Abort()

    # Build list of (installed_meta, index_entry) pairs to check
    installed = store.list_installed()
    if package:
        installed = [p for p in installed if p.get("name", "").lower() == package.lower()]
        if not installed:
            console.print(f"[yellow]'{package}' is not installed.[/yellow]")
            raise click.exceptions.Exit(1)

    updates_available: list[dict] = []
    up_to_date: list[str] = []
    not_in_index: list[str] = []
    skipped_pinned: list[str] = []

    from core.pins import PinManager
    pm = PinManager()

    for meta in installed:
        name = meta.get("name", "")
        current_ver = meta.get("version", "0.0.0")

        # Respect pins
        if pm.is_pinned(name) and update_all:
            skipped_pinned.append(f"{name} v{current_ver}")
            continue

        entry = manager.find(name)

        if entry is None:
            not_in_index.append(name)
            continue

        latest_ver = entry.get("version", "0.0.0")
        try:
            if Version(latest_ver) > Version(current_ver):
                updates_available.append({
                    "meta": meta,
                    "entry": entry,
                    "current": current_ver,
                    "latest": latest_ver,
                })
            else:
                up_to_date.append(f"{name} v{current_ver}")
        except InvalidVersion:
            up_to_date.append(f"{name} v{current_ver} (version parse failed)")

    # --- Summary ---
    if not updates_available:
        console.print("[bold green]✓ All packages are up to date.[/bold green]")
        if skipped_pinned:
            console.print(f"  [dim]Skipped {len(skipped_pinned)} pinned package(s): {', '.join(skipped_pinned)}[/dim]")
        if up_to_date and cfg.verbose:
            for name in up_to_date:
                console.print(f"  [dim]up to date: {name}[/dim]")
        return

    table = Table(
        title="Updates Available",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Package", style="bold cyan")
    table.add_column("Installed", style="yellow")
    table.add_column("Latest", style="green")
    table.add_column("Language", style="dim")

    for u in updates_available:
        table.add_row(
            u["meta"]["name"],
            u["current"],
            u["latest"],
            u["meta"].get("language", "—"),
        )

    console.print(table)

    if dry_run:
        console.print("[dim]Dry run — nothing installed.[/dim]")
        return

    # --- Perform updates by delegating to install logic ---
    from click.testing import CliRunner
    from cli.commands.install import install_cmd

    updated = 0
    for u in updates_available:
        name = u["meta"]["name"]
        console.print(f"\nUpdating [bold]{name}[/bold] "
                      f"v{u['current']} → v{u['latest']}...")
        # Evict old version first
        store.evict(u["meta"]["language"], name, u["current"])
        # Invoke install via the same context
        try:
            ctx.invoke(install_cmd, package=name, trust=False, no_build=False, force=True)
            updated += 1
        except Exception as exc:
            console.print(f"  [red]Failed to update {name}: {exc}[/red]")

    console.print(
        f"\n[bold green]✓ Updated {updated}/{len(updates_available)} package(s).[/bold green]"
    )
