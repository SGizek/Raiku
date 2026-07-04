"""
raiku verify <package>

Re-verify the integrity of a single installed package by recomputing
its SHA-256 hash and comparing against the index. Faster than running
a full raiku audit when you only care about one package.
"""
from __future__ import annotations

import hashlib

import click
from rich.console import Console
from rich.panel import Panel

from core.config import RaikuConfig
from core.constants import HASH_ALGORITHM
from index.index_manager import IndexManager, IndexError
from installer.cache_store import CacheStore


@click.command("verify")
@click.argument("package")
@click.option("--version", "pkg_version", default=None,
              help="Specific version to verify.")
@click.pass_context
def verify_cmd(ctx: click.Context, package: str, pkg_version: str | None) -> None:
    """Re-verify the integrity of an installed PACKAGE."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    installed = store.list_installed()

    matches = [
        p for p in installed
        if p.get("name", "").lower() == package.lower()
        and (pkg_version is None or p.get("version") == pkg_version)
    ]

    if not matches:
        console.print(f"[red]'{package}' is not installed.[/red]")
        raise click.exceptions.Exit(1)

    meta = sorted(matches, key=lambda m: m.get("version", ""), reverse=True)[0]
    name    = meta["name"]
    version = meta["version"]
    lang    = meta["language"]

    pkg_dir = store.get_package_dir(lang, name, version)
    if pkg_dir is None:
        console.print(f"[red]Cache directory missing for '{name}'.[/red]")
        raise click.exceptions.Exit(1)

    toml_path = pkg_dir / "raiku.toml"
    if not toml_path.exists():
        console.print(f"[red]raiku.toml missing from cache for '{name}'.[/red]")
        raise click.exceptions.Exit(1)

    actual_hash = hashlib.new(HASH_ALGORITHM, toml_path.read_bytes()).hexdigest()

    # Get expected hash from index
    try:
        manager = IndexManager(index_url=cfg.index_url)
        entry = manager.find(name)
        expected_hash = entry.get("sha256") if entry else None
    except IndexError:
        expected_hash = None

    console.print(f"\n  Package:  [bold]{name}[/bold] v{version} [{lang}]")
    console.print(f"  File:     {toml_path}")
    console.print(f"  Actual:   [dim]{actual_hash}[/dim]")

    if expected_hash is None:
        console.print(f"  Expected: [yellow]not recorded in index[/yellow]")
        console.print(Panel(
            f"[yellow]⚠ Cannot verify '{name}' — no hash recorded in index.[/yellow]\n"
            "Run [cyan]raiku sync[/cyan] to refresh the index.",
            border_style="yellow",
        ))
    elif actual_hash == expected_hash:
        console.print(f"  Expected: [dim]{expected_hash}[/dim]")
        console.print(Panel(
            f"[bold green]✓ '{name}' v{version} passed integrity check.[/bold green]",
            border_style="green",
        ))
    else:
        console.print(f"  Expected: [red]{expected_hash}[/red]")
        console.print(Panel(
            f"[bold red]✗ INTEGRITY FAILURE: '{name}' v{version}[/bold red]\n\n"
            "The cached raiku.toml does not match the hash in the index.\n"
            "The package may have been tampered with after installation.\n\n"
            f"Run [cyan]raiku uninstall {name} --yes && raiku install {name}[/cyan] "
            "to reinstall cleanly.",
            border_style="red",
        ))
        raise click.exceptions.Exit(1)
