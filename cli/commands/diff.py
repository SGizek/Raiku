"""
raiku diff <package>

Compare the installed version of a package against the latest version
in the index. Shows version numbers, what changed in the changelog,
and whether an update is available.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from packaging.version import Version, InvalidVersion

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("diff")
@click.argument("package")
@click.pass_context
def diff_cmd(ctx: click.Context, package: str) -> None:
    """Show what changed between the installed and latest version of PACKAGE."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    manager = IndexManager(index_url=cfg.index_url)

    # --- Get installed meta ---
    installed_list = store.list_installed()
    installed = next(
        (p for p in installed_list if p.get("name", "").lower() == package.lower()),
        None,
    )

    # --- Get index entry ---
    try:
        entry = manager.find(package)
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]  Run [cyan]raiku sync[/cyan] first.")
        raise click.Abort()

    if entry is None and installed is None:
        console.print(f"[red]Package '{package}' not found in index or local cache.[/red]")
        raise click.exceptions.Exit(1)

    # --- Versions ---
    installed_ver = installed.get("version", "not installed") if installed else "not installed"
    latest_ver    = entry.get("version", "unknown") if entry else "unknown"

    try:
        needs_update = installed and entry and Version(latest_ver) > Version(installed_ver)
    except InvalidVersion:
        needs_update = False

    # --- Header table ---
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("K", style="bold cyan")
    table.add_column("V")

    table.add_row("Package",   package)
    table.add_row("Installed", f"[yellow]{installed_ver}[/yellow]")
    table.add_row(
        "Latest",
        f"[green]{latest_ver}[/green]"
        if not needs_update else
        f"[bold green]{latest_ver} ← update available[/bold green]"
    )
    if entry:
        table.add_row("Language",  entry.get("language", "—"))
        table.add_row("Author",    entry.get("author", "—"))

    console.print(Panel(table, title=f"[bold]diff: {package}[/bold]", border_style="cyan"))

    # --- Changelog from cached version.yml ---
    _show_changelog(console, store, installed, installed_ver, "Installed version changelog")

    # --- If up to date ---
    if not needs_update:
        if installed_ver == latest_ver:
            console.print(f"[green]✓ {package} is up to date (v{latest_ver}).[/green]")
        else:
            console.print(f"[dim]{package} v{installed_ver} — no newer version in index.[/dim]")
        return

    console.print(
        f"\nRun [cyan]raiku update {package}[/cyan] to upgrade "
        f"v{installed_ver} → v{latest_ver}"
    )


def _show_changelog(
    console: Console,
    store: CacheStore,
    meta: dict | None,
    version: str,
    title: str,
) -> None:
    if meta is None:
        return
    pkg_dir = store.get_package_dir(meta["language"], meta["name"], meta["version"])
    if pkg_dir is None:
        return
    yml_path = pkg_dir / "version.yml"
    if not yml_path.exists():
        return
    try:
        import yaml
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
        changelog = data.get("changelog", [])
        stability = data.get("stability_level", "")
        if not changelog:
            return
        lines = changelog if isinstance(changelog, list) else [changelog]
        text = "\n".join(f"  • {line}" for line in lines)
        text += f"\n\n  [dim]Stability: {stability}[/dim]"
        console.print(Panel(text, title=f"[bold]{title} (v{version})[/bold]", border_style="dim"))
    except Exception:
        pass
