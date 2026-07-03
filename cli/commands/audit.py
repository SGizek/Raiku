"""
raiku audit

Scans all installed packages and verifies that their cached raiku.toml
SHA-256 hashes still match what the index declares. Flags tampering or
corruption after installation.
"""
from __future__ import annotations

import hashlib
import json

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config import RaikuConfig
from core.constants import HASH_ALGORITHM
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("audit")
@click.option("--language", "-l", default=None, help="Audit only one language.")
@click.option("--fix", is_flag=True, default=False,
              help="Evict packages that fail audit (they can be reinstalled cleanly).")
@click.pass_context
def audit_cmd(ctx: click.Context, language: str | None, fix: bool) -> None:
    """Verify cached package integrity against the index."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("[bold cyan]Raiku Audit[/bold cyan] — verifying package integrity\n")

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

    if not installed:
        console.print("[yellow]No packages installed to audit.[/yellow]")
        return

    results: list[dict] = []

    for meta in installed:
        name    = meta.get("name", "")
        version = meta.get("version", "")
        lang    = meta.get("language", "")

        pkg_dir = store.get_package_dir(lang, name, version)
        if pkg_dir is None:
            results.append({"name": name, "version": version, "lang": lang,
                             "status": "MISSING", "detail": "Cache directory not found"})
            continue

        toml_path = pkg_dir / "raiku.toml"
        if not toml_path.exists():
            results.append({"name": name, "version": version, "lang": lang,
                             "status": "MISSING", "detail": "raiku.toml not in cache"})
            continue

        # Compute actual hash
        actual_hash = hashlib.new(HASH_ALGORITHM, toml_path.read_bytes()).hexdigest()

        # Get expected hash from index
        entry = manager.find(name)
        expected_hash = entry.get("sha256") if entry else None

        if expected_hash is None:
            results.append({"name": name, "version": version, "lang": lang,
                             "status": "NO_HASH",
                             "detail": "No hash in index — cannot verify"})
        elif actual_hash == expected_hash:
            results.append({"name": name, "version": version, "lang": lang,
                             "status": "OK", "detail": ""})
        else:
            results.append({"name": name, "version": version, "lang": lang,
                             "status": "FAIL",
                             "detail": f"expected {expected_hash[:16]}… got {actual_hash[:16]}…"})
            if fix:
                store.evict(lang, name, version)

    # --- Report ---
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package",  style="bold cyan")
    table.add_column("Version",  style="dim")
    table.add_column("Language", style="dim")
    table.add_column("Status",   min_width=10)
    table.add_column("Detail",   style="dim")

    failures = 0
    warnings = 0

    for r in sorted(results, key=lambda x: x["name"]):
        status = r["status"]
        if status == "OK":
            status_str = "[bold green]✓ OK[/bold green]"
        elif status == "NO_HASH":
            status_str = "[yellow]? NO HASH[/yellow]"
            warnings += 1
        elif status in ("FAIL", "MISSING"):
            status_str = "[bold red]✗ FAIL[/bold red]"
            failures += 1
        else:
            status_str = status

        table.add_row(r["name"], r["version"], r["lang"], status_str, r["detail"])

    console.print(table)
    console.print()

    if failures:
        msg = f"[bold red]✗ {failures} package(s) failed integrity check.[/bold red]"
        if fix:
            msg += " Evicted from cache — run [cyan]raiku install <name>[/cyan] to reinstall."
        else:
            msg += " Run [cyan]raiku audit --fix[/cyan] to remove corrupted packages."
        console.print(Panel(msg, border_style="red"))
    elif warnings:
        console.print(
            f"[yellow]{warnings} package(s) have no recorded hash and could not be verified.[/yellow]"
        )
    else:
        console.print(
            f"[bold green]✓ All {len(results)} package(s) passed integrity audit.[/bold green]"
        )
