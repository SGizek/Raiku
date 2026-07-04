"""
raiku run <package> <command> [args...]

Execute a command from within an installed package's cache directory.
Like npx — finds the cached package and runs the command inside it.

Examples:
    raiku run fast-math python src/fast_math.py
    raiku run cmatrix ./cmatrix
    raiku run zigutils zig build test
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from core.config import RaikuConfig
from installer.cache_store import CacheStore


@click.command("run", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("package")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--version", "pkg_version", default=None,
              help="Specific installed version to use.")
@click.pass_context
def run_cmd(
    ctx: click.Context,
    package: str,
    args: tuple[str, ...],
    pkg_version: str | None,
) -> None:
    """Execute a command inside an installed package's directory.

    \b
    Examples:
      raiku run fast-math python src/fast_math.py
      raiku run cmatrix ./cmatrix
      raiku run zigutils zig build test
    """
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if not args:
        console.print(
            "[red]No command specified.[/red]\n"
            "Usage: raiku run <package> <command> [args...]\n"
            "Example: raiku run fast-math python src/fast_math.py"
        )
        raise click.exceptions.Exit(1)

    store = CacheStore(cfg.cache_dir)
    installed = store.list_installed()

    matches = [
        p for p in installed
        if p.get("name", "").lower() == package.lower()
        and (pkg_version is None or p.get("version") == pkg_version)
    ]

    if not matches:
        console.print(
            f"[red]Package '{package}' is not installed.[/red] "
            f"Run [cyan]raiku install {package}[/cyan] first."
        )
        raise click.exceptions.Exit(1)

    # Use the latest installed version if multiple
    meta = sorted(matches, key=lambda m: m.get("version", ""), reverse=True)[0]
    pkg_dir = store.get_package_dir(meta["language"], meta["name"], meta["version"])

    if pkg_dir is None:
        console.print(f"[red]Cache directory for '{package}' not found.[/red]")
        raise click.exceptions.Exit(1)

    if cfg.verbose:
        console.print(
            f"[dim]Running in:[/dim] {pkg_dir}\n"
            f"[dim]Command:[/dim] {' '.join(args)}"
        )

    # Build safe environment (inherit from host but add package dir)
    env = os.environ.copy()
    env["RAIKU_PKG"] = meta["name"]
    env["RAIKU_PKG_VERSION"] = meta["version"]
    env["RAIKU_PKG_LANG"] = meta["language"]
    env["RAIKU_PKG_DIR"] = str(pkg_dir)

    cmd = list(args)
    if sys.platform == "win32":
        result = subprocess.run(cmd, cwd=str(pkg_dir), env=env, shell=False)
    else:
        result = subprocess.run(cmd, cwd=str(pkg_dir), env=env)

    raise click.exceptions.Exit(result.returncode)
