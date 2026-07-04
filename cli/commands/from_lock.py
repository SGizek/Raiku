"""
raiku from-lock

Install the exact package versions recorded in raiku.lock.
Guarantees reproducible installs across machines — every version
is locked, no automatic resolution to latest.

Usage:
    raiku from-lock                    # reads ./raiku.lock
    raiku from-lock --file my.lock     # reads a specific lock file
    raiku from-lock --no-build         # cache only, skip builds
    raiku from-lock --trust            # skip build confirmations
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from core.config import RaikuConfig
from core.lockfile import LockFile, LOCK_FILENAME
from index.index_manager import IndexManager, IndexError


@click.command("from-lock")
@click.option("--file", "-f", "lock_file", default=LOCK_FILENAME,
              help=f"Lock file to read (default: {LOCK_FILENAME}).")
@click.option("--trust", is_flag=True, default=False,
              help="Skip build command confirmation for all packages.")
@click.option("--no-build", is_flag=True, default=False,
              help="Download and cache only; skip all build commands.")
@click.option("--force", is_flag=True, default=False,
              help="Reinstall packages even if already cached.")
@click.pass_context
def from_lock_cmd(
    ctx: click.Context,
    lock_file: str,
    trust: bool,
    no_build: bool,
    force: bool,
) -> None:
    """Install exact package versions from a raiku.lock file."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # Readonly guard
    if getattr(cfg, "readonly", False):
        console.print(
            "[red]Readonly mode is enabled.[/red] "
            "Run [cyan]raiku config set readonly false[/cyan] to allow installs."
        )
        raise click.exceptions.Exit(1)

    lock_path = Path(lock_file)
    if not lock_path.exists():
        console.print(
            f"[red]Lock file '{lock_file}' not found.[/red]\n"
            "Run [cyan]raiku install <package> --lock[/cyan] to create one."
        )
        raise click.exceptions.Exit(1)

    lock = LockFile(lock_path)
    packages = lock.all_packages()

    if not packages:
        console.print("[yellow]Lock file is empty — nothing to install.[/yellow]")
        return

    console.print(
        f"[bold cyan]Installing {len(packages)} package(s) from {lock_file}[/bold cyan]\n"
    )

    # Load index for entry metadata (path, author, etc.)
    manager = IndexManager(index_url=cfg.index_url)
    try:
        manager.load()
        index_available = True
    except IndexError:
        index_available = False
        console.print(
            "[yellow]Index not loaded — run raiku sync for best results.[/yellow]"
        )

    from installer.cache_store import CacheStore
    from cli.commands.install import _install_one

    store = CacheStore(cfg.cache_dir)
    success = 0
    skipped = 0
    failed  = 0

    for pkg_name, locked in packages.items():
        locked_version = locked["version"]
        locked_lang    = locked.get("language", "")

        # Already cached at locked version — respect --force
        if store.is_cached(locked_lang, pkg_name, locked_version) and not force:
            console.print(
                f"  [green]✓[/green] [bold]{pkg_name}[/bold] v{locked_version} "
                "already installed"
            )
            skipped += 1
            continue

        # Build an entry dict — prefer index data, fall back to lock data
        if index_available:
            entry = manager.find(pkg_name)
        else:
            entry = None

        if entry is None:
            # Construct a minimal entry from the lock record
            entry = {
                "name":     pkg_name,
                "version":  locked_version,
                "language": locked_lang,
                "path":     locked.get("path", ""),
                "sha256":   locked.get("sha256", ""),
                "author":   "",
            }
        else:
            # Override index version with locked version for exact reproducibility
            entry = dict(entry)
            entry["version"] = locked_version

        try:
            _install_one(
                ctx, cfg, console,
                pkg_name, entry,
                trust, no_build, force,
                use_lock=False,   # don't re-write the lock we just read
            )
            success += 1
        except SystemExit as exc:
            if exc.code != 0:
                console.print(f"  [red]Failed: {pkg_name}[/red]")
                failed += 1
        except Exception as exc:
            console.print(f"  [red]Failed: {pkg_name}: {exc}[/red]")
            failed += 1

    console.print(
        f"\n[bold]Results:[/bold] "
        f"[green]{success} installed[/green]  "
        f"[dim]{skipped} already up to date[/dim]  "
        f"{'[red]' + str(failed) + ' failed[/red]' if failed else ''}"
    )
