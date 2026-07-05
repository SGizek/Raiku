"""
raiku repair

Scans the local cache for broken or incomplete package entries and
either reports them or removes them automatically.

A package entry is considered broken if any of the following are true:
  - The package directory exists but meta.json is missing
  - The package directory exists but raiku.toml is missing
  - The package directory is empty
  - The meta.json cannot be parsed as JSON
"""
from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from core.config import RaikuConfig
from core.cache import CacheManager


@click.command("repair")
@click.option("--fix", is_flag=True, default=False,
              help="Remove all broken cache entries (default: report only).")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt when using --fix.")
@click.pass_context
def repair_cmd(ctx: click.Context, fix: bool, yes: bool) -> None:
    """Scan and clean broken or incomplete cache entries."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("[bold cyan]Raiku Repair[/bold cyan] — scanning cache...\n")

    manager = CacheManager(cfg.cache_dir)
    broken: list[dict] = []

    if not cfg.cache_dir.exists():
        console.print("[dim]Cache directory does not exist — nothing to repair.[/dim]")
        return

    for lang_dir in sorted(cfg.cache_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        for pkg_dir in sorted(lang_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue
            for ver_dir in sorted(pkg_dir.iterdir()):
                if not ver_dir.is_dir():
                    continue
                issues = _check_entry(ver_dir)
                if issues:
                    broken.append({
                        "language": lang_dir.name,
                        "name":     pkg_dir.name,
                        "version":  ver_dir.name,
                        "path":     ver_dir,
                        "issues":   issues,
                    })

    if not broken:
        console.print("[bold green]✓ Cache is clean — no broken entries found.[/bold green]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="bold cyan")
    table.add_column("Version", style="dim")
    table.add_column("Language", style="dim")
    table.add_column("Issues", style="yellow")

    for entry in broken:
        table.add_row(
            entry["name"],
            entry["version"],
            entry["language"],
            "; ".join(entry["issues"]),
        )

    console.print(table)
    console.print(f"\n[yellow]Found {len(broken)} broken cache entry/entries.[/yellow]")

    if not fix:
        console.print(
            "\nRun [cyan]raiku repair --fix[/cyan] to remove them.\n"
            "They can be cleanly reinstalled with [cyan]raiku install <name>[/cyan]."
        )
        return

    if not yes:
        if not Confirm.ask(f"\nRemove {len(broken)} broken entries?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    removed = 0
    for entry in broken:
        ok = manager.evict(entry["language"], entry["name"], entry["version"])
        if ok:
            console.print(
                f"  [green]✓[/green] Removed {entry['name']} v{entry['version']}"
            )
            removed += 1
        else:
            console.print(
                f"  [red]✗[/red] Could not remove {entry['name']} v{entry['version']}"
            )

    console.print(
        f"\n[bold green]Repair complete.[/bold green] "
        f"{removed}/{len(broken)} broken entries removed."
    )


def _check_entry(ver_dir) -> list[str]:
    """Return a list of issue strings for a cache version directory."""
    issues = []

    contents = list(ver_dir.iterdir())
    if not contents:
        issues.append("empty directory")
        return issues

    meta_path = ver_dir / "meta.json"
    if not meta_path.exists():
        issues.append("missing meta.json")
    else:
        try:
            json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append("corrupt meta.json")

    toml_path = ver_dir / "raiku.toml"
    if not toml_path.exists():
        issues.append("missing raiku.toml")

    return issues
