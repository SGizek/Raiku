"""
raiku index

Index management commands:
  raiku index --rebuild   Walk UserSub/ and regenerate index/index.json
  raiku index --stats     Show stats about the current index
  raiku index --check     Validate every entry in the index
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config import RaikuConfig
from core.constants import (
    SUPPORTED_LANGUAGES, RAIKU_TOML, VERSION_YML, HASH_ALGORITHM
)
from index.index_manager import IndexManager, IndexError
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError


@click.command("index")
@click.option("--rebuild", is_flag=True, default=False,
              help="Scan UserSub/ and regenerate index/index.json.")
@click.option("--stats", is_flag=True, default=False,
              help="Show statistics about the current index.")
@click.option("--check", is_flag=True, default=False,
              help="Validate every entry in the index.")
@click.option(
    "--root", default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Repository root directory (default: current directory).",
)
@click.option("--dry-run", is_flag=True, default=False,
              help="With --rebuild: print the new index without writing it.")
@click.pass_context
def index_cmd(
    ctx: click.Context,
    rebuild: bool,
    stats: bool,
    check: bool,
    root: Path,
    dry_run: bool,
) -> None:
    """Manage the Raiku package index."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if not any([rebuild, stats, check]):
        console.print(
            "Specify an action:\n"
            "  [cyan]raiku index --rebuild[/cyan]  — regenerate index from UserSub/\n"
            "  [cyan]raiku index --stats[/cyan]    — show index statistics\n"
            "  [cyan]raiku index --check[/cyan]    — validate all index entries"
        )
        return

    if rebuild:
        _do_rebuild(console, root, dry_run)
    if stats:
        _do_stats(console, cfg)
    if check:
        _do_check(console, cfg, root)


# ---------------------------------------------------------------------------
# Rebuild
# ---------------------------------------------------------------------------

def _do_rebuild(console: Console, root: Path, dry_run: bool) -> None:
    usersub = root / "UserSub"
    if not usersub.exists():
        console.print(f"[red]UserSub/ not found at {root}[/red]")
        raise click.exceptions.Exit(1)

    console.print(f"[bold cyan]Scanning[/bold cyan] {usersub} ...")

    packages: list[dict[str, Any]] = []
    errors: list[str] = []

    for lang in SUPPORTED_LANGUAGES:
        lang_dir = usersub / lang
        if not lang_dir.exists():
            continue
        for pkg_dir in sorted(lang_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue
            toml_path = pkg_dir / RAIKU_TOML
            if not toml_path.exists():
                errors.append(f"{pkg_dir.relative_to(root)}: missing raiku.toml")
                continue
            try:
                manifest = parse_raiku_toml(pkg_dir)
            except TomlParseError as exc:
                errors.append(f"{pkg_dir.name}: {exc}")
                continue

            # Compute sha256 of raiku.toml
            sha256 = hashlib.new(HASH_ALGORITHM, toml_path.read_bytes()).hexdigest()

            entry: dict[str, Any] = {
                "name": manifest["name"],
                "version": manifest["version"],
                "language": manifest["language"],
                "author": manifest.get("author", ""),
                "description": manifest.get("description", ""),
                "path": f"UserSub/{lang}/{pkg_dir.name}",
                "sha256": sha256,
            }

            # Include tags if present
            if "tags" in manifest:
                entry["tags"] = manifest["tags"]

            # Include license / homepage
            for opt in ("license", "homepage", "dependencies"):
                if opt in manifest:
                    entry[opt] = manifest[opt]

            packages.append(entry)
            console.print(f"  [green]✓[/green] {manifest['name']} v{manifest['version']} [{lang}]")

    if errors:
        console.print(f"\n[yellow]⚠ {len(errors)} package(s) skipped:[/yellow]")
        for e in errors:
            console.print(f"  [dim]- {e}[/dim]")

    new_index = {
        "schema_version": "1.0.0",
        "generated_by": "raiku index --rebuild",
        "packages": packages,
    }

    index_json = json.dumps(new_index, indent=2)

    if dry_run:
        console.print("\n[dim]Dry run — index not written:[/dim]")
        console.print(index_json)
        return

    out_path = root / "index" / "index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(index_json, encoding="utf-8")

    console.print(
        f"\n[bold green]✓ index/index.json rebuilt[/bold green] — "
        f"{len(packages)} package(s) indexed."
    )


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def _do_stats(console: Console, cfg: RaikuConfig) -> None:
    manager = IndexManager(index_url=cfg.index_url)
    try:
        stats = manager.stats()
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]")
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")
    table.add_row("Total packages", str(stats["total"]))
    table.add_row("Schema version", str(stats["schema_version"]))

    if stats.get("synced_at"):
        import datetime
        dt = datetime.datetime.fromtimestamp(stats["synced_at"]).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row("Last synced", dt)

    console.print(Panel(table, title="Index Statistics"))

    lang_table = Table(show_header=True, header_style="bold magenta")
    lang_table.add_column("Language", style="cyan")
    lang_table.add_column("Packages", justify="right", style="green")
    for lang, count in sorted(stats["by_language"].items()):
        lang_table.add_row(lang, str(count))
    console.print(lang_table)


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

def _do_check(console: Console, cfg: RaikuConfig, root: Path) -> None:
    manager = IndexManager(index_url=cfg.index_url)
    try:
        data = manager.load()
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]")
        return

    packages = data.get("packages", [])
    errors = 0

    for pkg in packages:
        name = pkg.get("name", "?")
        pkg_path = root / pkg.get("path", "")
        issues: list[str] = []

        if not pkg_path.exists():
            issues.append(f"path does not exist: {pkg.get('path')}")
        else:
            toml_path = pkg_path / RAIKU_TOML
            if toml_path.exists() and pkg.get("sha256"):
                actual = hashlib.new(HASH_ALGORITHM, toml_path.read_bytes()).hexdigest()
                if actual != pkg["sha256"]:
                    issues.append(
                        f"sha256 mismatch (index: {pkg['sha256'][:12]}… "
                        f"actual: {actual[:12]}…)"
                    )

        if issues:
            for issue in issues:
                console.print(f"  [red]✗[/red] {name}: {issue}")
            errors += 1
        else:
            if cfg.verbose:
                console.print(f"  [green]✓[/green] {name}")

    if errors:
        console.print(f"\n[red]{errors} package(s) have index issues.[/red]")
    else:
        console.print(
            f"[bold green]✓ All {len(packages)} index entries are valid.[/bold green]"
        )
