"""
raiku rollback <package>

Reinstall the previous cached version of a package. Useful when an
update breaks something — Raiku keeps old versions in cache until
explicitly evicted, so rolling back is instant with no network needed.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from packaging.version import Version, InvalidVersion

from core.config import RaikuConfig
from installer.cache_store import CacheStore


@click.command("rollback")
@click.argument("package")
@click.option("--to", "target_version", default=None,
              help="Version to roll back to (default: previous cached version).")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt.")
@click.pass_context
def rollback_cmd(ctx: click.Context, package: str,
                 target_version: str | None, yes: bool) -> None:
    """Roll back PACKAGE to its previous installed version."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    installed = store.list_installed()

    # Find all cached versions of this package
    versions = [
        p for p in installed
        if p.get("name", "").lower() == package.lower()
    ]

    if not versions:
        console.print(f"[red]'{package}' has no cached versions.[/red]")
        raise click.exceptions.Exit(1)

    # Sort versions descending
    try:
        versions.sort(key=lambda p: Version(p.get("version", "0")), reverse=True)
    except InvalidVersion:
        versions.sort(key=lambda p: p.get("version", ""), reverse=True)

    current = versions[0]

    if len(versions) == 1 and target_version is None:
        console.print(
            f"[yellow]Only one cached version of '{package}' "
            f"(v{current['version']}).[/yellow]\n"
            "Install a different version first, or use "
            "[cyan]raiku install <package> --force[/cyan]."
        )
        raise click.exceptions.Exit(1)

    # Determine rollback target
    if target_version:
        target = next(
            (v for v in versions if v.get("version") == target_version), None
        )
        if target is None:
            console.print(
                f"[red]Version '{target_version}' of '{package}' is not in cache.[/red]\n"
                "Available versions: " +
                ", ".join(v.get("version", "?") for v in versions)
            )
            raise click.exceptions.Exit(1)
    else:
        # Roll back to the version before the current one
        target = versions[1]

    if target["version"] == current["version"]:
        console.print(f"[yellow]Already at v{current['version']}.[/yellow]")
        return

    console.print(
        f"  Roll back [bold]{package}[/bold]: "
        f"v{current['version']} → v{target['version']}"
    )

    if not yes:
        if not Confirm.ask("Proceed with rollback?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    # The older version is already in cache — just switch the "current" marker
    # by evicting the newer one. The older one remains accessible.
    store.evict(current["language"], package, current["version"])

    target_meta = store.read_meta(target["language"], package, target["version"])
    if target_meta:
        console.print(
            f"[bold green]✓ Rolled back[/bold green] [bold]{package}[/bold] "
            f"to v{target['version']}."
        )
        console.print(
            f"  [dim]v{current['version']} removed from cache. "
            f"Reinstall with raiku install {package} --force.[/dim]"
        )
    else:
        console.print(
            f"[yellow]Evicted v{current['version']}, but v{target['version']} "
            f"metadata not found. Try raiku install {package}.[/yellow]"
        )
