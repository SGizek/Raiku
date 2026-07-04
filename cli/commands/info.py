"""
raiku info <package>

Shows full details for a package from the index, plus local install status.
"""
from __future__ import annotations

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import RaikuConfig
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("info")
@click.argument("package")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output as JSON.")
@click.option("--changelog", "show_changelog", is_flag=True, default=False,
              help="Show the full changelog from version.yml.")
@click.pass_context
def info_cmd(ctx: click.Context, package: str, as_json: bool, show_changelog: bool) -> None:
    """Show detailed information about PACKAGE."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    manager = IndexManager(index_url=cfg.index_url)

    try:
        entry = manager.find(package)
    except IndexError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        console.print("Run [cyan]raiku sync[/cyan] to download the index first.")
        raise click.Abort()

    if entry is None:
        console.print(f"[bold red]Package '{package}' not found in index.[/bold red]")
        console.print("Run [cyan]raiku search[/cyan] to browse available packages.")
        raise click.exceptions.Exit(1)

    # Check local install status
    store = CacheStore(cfg.cache_dir)
    installed = store.read_meta(
        entry["language"], entry["name"], entry["version"]
    )

    if as_json:
        output = dict(entry)
        output["installed"] = installed is not None
        if installed:
            output["installed_meta"] = installed
        console.print(json.dumps(output, indent=2))
        return

    # --- Rich display ---
    status = (
        f"[bold green]✓ Installed[/bold green] (v{installed['version']})"
        if installed
        else "[dim]Not installed[/dim]"
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan", min_width=18)
    table.add_column("Value", style="white")

    table.add_row("Name", entry.get("name", "—"))
    table.add_row("Version", entry.get("version", "—"))
    table.add_row("Language", entry.get("language", "—"))
    table.add_row("Author", entry.get("author", "—"))
    table.add_row("Description", entry.get("description", "—"))
    table.add_row("License", entry.get("license", "—"))
    table.add_row("Homepage", entry.get("homepage", "—"))
    table.add_row("Path", entry.get("path", "—"))
    table.add_row("SHA-256", entry.get("sha256", "[dim]not recorded[/dim]"))

    tags = entry.get("tags", [])
    if tags:
        table.add_row("Tags", ", ".join(tags))

    deps = entry.get("dependencies", [])
    table.add_row("Dependencies", ", ".join(deps) if deps else "none")
    table.add_row("Local status", status)

    if installed:
        import datetime
        ts = installed.get("installed_at")
        if ts:
            dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            table.add_row("Installed at", dt)

    console.print(Panel(
        table,
        title=f"[bold]{entry.get('name')}[/bold] — Package Info",
        border_style="cyan",
    ))

    # --- Changelog panel ---
    if show_changelog:
        store = CacheStore(cfg.cache_dir)
        pkg_dir = store.get_package_dir(
            entry["language"], entry["name"], entry["version"]
        )
        changelog_shown = False
        if pkg_dir:
            yml_path = pkg_dir / "version.yml"
            if yml_path.exists():
                try:
                    import yaml
                    data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
                    changelog = data.get("changelog", [])
                    stability = data.get("stability_level", "")
                    if changelog:
                        entries = changelog if isinstance(changelog, list) else [changelog]
                        text = "\n".join(f"  • {e}" for e in entries)
                        text += f"\n\n  [dim]Stability: {stability}[/dim]"
                        console.print(Panel(
                            text,
                            title=f"[bold]Changelog — v{entry.get('version')}[/bold]",
                            border_style="dim",
                        ))
                        changelog_shown = True
                except Exception:
                    pass
        if not changelog_shown:
            console.print(
                "[dim]Changelog not available — install the package first to read version.yml.[/dim]"
            )
