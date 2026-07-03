"""
raiku uninstall <package>

Removes a package from the local cache at ~/.raiku/cache/.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.prompt import Confirm

from core.config import RaikuConfig
from installer.cache_store import CacheStore
from index.index_manager import IndexManager, IndexError


@click.command("uninstall")
@click.argument("package")
@click.option(
    "--yes", "-y", is_flag=True, default=False,
    help="Skip confirmation prompt.",
)
@click.option(
    "--version", "pkg_version", default=None,
    help="Specific version to uninstall (default: all cached versions).",
)
@click.pass_context
def uninstall_cmd(
    ctx: click.Context,
    package: str,
    yes: bool,
    pkg_version: str | None,
) -> None:
    """Remove PACKAGE from the local cache."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    all_installed = store.list_installed()

    # Find matching entries
    matches = [
        p for p in all_installed
        if p.get("name", "").lower() == package.lower()
        and (pkg_version is None or p.get("version") == pkg_version)
    ]

    if not matches:
        console.print(
            f"[yellow]Package '{package}' is not installed"
            + (f" (version {pkg_version})" if pkg_version else "")
            + ".[/yellow]"
        )
        raise click.exceptions.Exit(1)

    # Show what will be removed
    for m in matches:
        console.print(
            f"  Will remove: [bold]{m['name']}[/bold] v{m['version']} "
            f"[{m.get('language', '?')}]"
        )

    if not yes:
        confirmed = Confirm.ask(
            f"\nRemove {len(matches)} package version(s)?",
            default=False,
        )
        if not confirmed:
            console.print("[dim]Aborted.[/dim]")
            return

    removed = 0
    for m in matches:
        ok = store.evict(m["language"], m["name"], m["version"])
        if ok:
            console.print(
                f"  [green]✓[/green] Removed [bold]{m['name']}[/bold] "
                f"v{m['version']} [{m.get('language')}]"
            )
            removed += 1
        else:
            console.print(
                f"  [red]✗[/red] Could not remove {m['name']} v{m['version']}"
            )

    console.print(f"\n[bold green]Done.[/bold green] {removed} version(s) removed.")
