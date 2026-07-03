"""
raiku install <package>
raiku install ./local-path

Full install flow:
  1. Load index.json  (skipped for local installs)
  2. Resolve dependencies (auto-install deps first)
  3. Validate schema compliance
  4. Fetch only the required package files (no full repo clone)
     - Real byte-level progress bars via rich.progress
  5. Cache locally at ~/.raiku/cache/
  6. Execute build_command safely (with user confirmation in safe mode)
  7. Update raiku.lock
  8. Confirm installation
"""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn,
)
from rich.prompt import Confirm

from core.config import RaikuConfig
from core.constants import RAIKU_TOML, VERSION_YML, HASH_ALGORITHM
from core.trust import TrustManager
from core.lockfile import LockFile, LOCK_FILENAME
from core.pins import PinManager
from index.index_manager import IndexManager, IndexError
from installer.fetcher import PackageFetcher, FetchError
from installer.cache_store import CacheStore
from installer.build_runner import BuildRunner, BuildError
from validator.schema_validator import SchemaValidator, SchemaValidationError
from validator.hash_validator import HashValidator, HashMismatchError
from validator.rules_checker import RulesChecker
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError


@click.command("install")
@click.argument("package")
@click.option("--trust", is_flag=True, default=False,
              help="Skip build command confirmation prompt.")
@click.option("--no-build", is_flag=True, default=False,
              help="Download and cache only; do not run build_command.")
@click.option("--force", "-f", is_flag=True, default=False,
              help="Reinstall even if already cached.")
@click.option("--no-deps", is_flag=True, default=False,
              help="Skip dependency resolution.")
@click.option("--lock", "use_lock", is_flag=True, default=False,
              help="Write/update raiku.lock in the current directory.")
@click.pass_context
def install_cmd(
    ctx: click.Context,
    package: str,
    trust: bool,
    no_build: bool,
    force: bool,
    no_deps: bool,
    use_lock: bool,
) -> None:
    """Install PACKAGE from the index, or from a local path (./path)."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # ------------------------------------------------------------------ Local install?
    is_local = package.startswith("./") or package.startswith(".\\") or Path(package).is_dir()

    if is_local:
        _install_local(ctx, cfg, console, Path(package), no_build, trust, use_lock)
        return

    # ------------------------------------------------------------------ Remote install
    _install_remote(ctx, cfg, console, package, trust, no_build, force, no_deps, use_lock)


# ===========================================================================
# Local install
# ===========================================================================

def _install_local(
    ctx: click.Context,
    cfg: RaikuConfig,
    console: Console,
    pkg_dir: Path,
    no_build: bool,
    trust: bool,
    use_lock: bool,
) -> None:
    if not pkg_dir.exists():
        console.print(f"[red]Path '{pkg_dir}' does not exist.[/red]")
        raise click.exceptions.Exit(1)

    console.print(f"[bold cyan]Raiku[/bold cyan] installing from local path: [dim]{pkg_dir.resolve()}[/dim]")

    # Validate
    sv = SchemaValidator()
    rc = RulesChecker()

    try:
        manifest = parse_raiku_toml(pkg_dir)
        sv.validate_raiku_toml(manifest)
    except (TomlParseError, SchemaValidationError) as exc:
        console.print(f"[red]raiku.toml error:[/red] {exc}")
        raise click.exceptions.Exit(1)

    try:
        version_data = parse_version_yml(pkg_dir)
        sv.validate_version_yml(version_data)
    except (YamlParseError, SchemaValidationError) as exc:
        console.print(f"[red]version.yml error:[/red] {exc}")
        raise click.exceptions.Exit(1)

    violations = rc.check(pkg_dir, manifest)
    if violations:
        for v in violations:
            console.print(f"  [red]✗[/red] {v}")
        raise click.exceptions.Exit(1)

    name     = manifest["name"]
    version  = manifest["version"]
    language = manifest["language"]

    # Copy to cache
    store = CacheStore(cfg.cache_dir)
    files: dict[str, bytes] = {}
    for fname in (RAIKU_TOML, VERSION_YML, "README.md"):
        fpath = pkg_dir / fname
        if fpath.exists():
            files[fname] = fpath.read_bytes()

    sha256 = hashlib.new(HASH_ALGORITHM, files[RAIKU_TOML]).hexdigest()
    fake_entry = {"name": name, "version": version, "language": language,
                  "path": str(pkg_dir), "sha256": sha256,
                  "author": manifest.get("author", "")}
    store.store_package(language, name, version, files, fake_entry)
    pkg_cache_dir = store.get_package_dir(language, name, version)
    console.print(f"  [green]✓[/green] Cached at: {pkg_cache_dir}")

    _run_build(console, cfg, manifest, pkg_cache_dir, name, trust, no_build)

    if use_lock:
        lock = LockFile(Path(LOCK_FILENAME))
        lock.add(fake_entry)
        console.print(f"  [green]✓[/green] Lock file updated")

    console.print(f"\n[bold green]✓ Installed[/bold green] [bold]{name}[/bold] v{version} [{language}] (local)")


# ===========================================================================
# Remote install
# ===========================================================================

def _install_remote(
    ctx: click.Context,
    cfg: RaikuConfig,
    console: Console,
    package: str,
    trust: bool,
    no_build: bool,
    force: bool,
    no_deps: bool,
    use_lock: bool,
) -> None:
    console.print(f"[bold cyan]Raiku[/bold cyan] installing [bold]{package}[/bold]...")

    manager = IndexManager(index_url=cfg.index_url)
    try:
        entry = manager.find(package)
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]  Run [cyan]raiku sync[/cyan] first.")
        raise click.Abort()

    if entry is None:
        console.print(f"[red]Package '{package}' not found.[/red]")
        raise click.exceptions.Exit(1)

    # ------------------------------------------------------------------ Dependency resolution
    install_order = [package]
    if not no_deps:
        from core.resolver import DependencyResolver, DependencyError
        resolver = DependencyResolver(manager)
        try:
            install_order = resolver.resolve(package)
        except DependencyError as exc:
            console.print(f"[red]Dependency error:[/red] {exc}")
            raise click.exceptions.Exit(1)

        deps = [p for p in install_order if p != package]
        if deps:
            console.print(f"  Dependencies: [cyan]{', '.join(deps)}[/cyan]")
            for dep in deps:
                dep_entry = manager.find(dep)
                if dep_entry:
                    _install_one(ctx, cfg, console, dep, dep_entry, trust, no_build, force, use_lock)

    # ------------------------------------------------------------------ Install main package
    _install_one(ctx, cfg, console, package, entry, trust, no_build, force, use_lock)


def _install_one(
    ctx: click.Context,
    cfg: RaikuConfig,
    console: Console,
    package: str,
    entry: dict,
    trust: bool,
    no_build: bool,
    force: bool,
    use_lock: bool,
) -> None:
    name     = entry["name"]
    version  = entry["version"]
    language = entry["language"]
    pkg_path = entry["path"]
    expected_sha256 = entry.get("sha256")

    store = CacheStore(cfg.cache_dir)
    if store.is_cached(language, name, version) and not force:
        console.print(
            f"  [green]✓[/green] [bold]{name}[/bold] v{version} already installed. "
            "(--force to reinstall)"
        )
        return

    console.print(
        f"  [dim]→[/dim] [bold]{name}[/bold] v{version} "
        f"[{language}] by {entry.get('author', 'unknown')}"
    )

    # ------------------------------------------------------------------ Fetch with progress
    fetcher = PackageFetcher(raw_base_url=cfg.raw_base_url)
    files: dict[str, bytes] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"  Fetching {name}...", total=None)

        def on_progress(downloaded: int, total: int, label: str) -> None:
            if total > 0:
                progress.update(task, total=total, completed=downloaded,
                                description=f"  {label}")

        try:
            files = fetcher.fetch_package(pkg_path, progress_callback=on_progress)
        except FetchError as exc:
            console.print(f"  [red]Fetch error:[/red] {exc}")
            raise click.Abort()

    console.print(f"  [green]✓[/green] Downloaded {len(files)} file(s)")

    # ------------------------------------------------------------------ Validate
    sv = SchemaValidator()
    hv = HashValidator()

    if RAIKU_TOML not in files:
        console.print("[red]raiku.toml missing from downloaded files.[/red]")
        raise click.Abort()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for fname, content in files.items():
            dest = tmp_path / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

        try:
            manifest     = parse_raiku_toml(tmp_path)
            version_data = parse_version_yml(tmp_path) if VERSION_YML in files else None
            sv.validate_raiku_toml(manifest)
            if version_data:
                sv.validate_version_yml(version_data)
        except (TomlParseError, YamlParseError, SchemaValidationError) as exc:
            console.print(f"  [red]Validation error:[/red] {exc}")
            raise click.Abort()

    # Hash check
    try:
        hv.verify_bytes(name, files[RAIKU_TOML], expected_sha256)
        if expected_sha256:
            console.print(f"  [green]✓[/green] Hash verified")
        else:
            console.print(f"  [yellow]⚠[/yellow] No hash recorded — skipping integrity check")
    except HashMismatchError as exc:
        console.print(f"  [red]Security alert:[/red] {exc}")
        raise click.Abort()

    # ------------------------------------------------------------------ Cache
    store.store_package(language, name, version, files, entry)
    pkg_dir = store.get_package_dir(language, name, version)
    console.print(f"  [green]✓[/green] Cached at: {pkg_dir}")

    # ------------------------------------------------------------------ Build
    _run_build(console, cfg, manifest, pkg_dir, name, trust, no_build)

    # ------------------------------------------------------------------ Lock file
    if use_lock:
        lock = LockFile(Path(LOCK_FILENAME))
        lock.add(entry)
        console.print(f"  [green]✓[/green] Lock file updated")

    console.print(
        f"\n[bold green]✓ Installed[/bold green] [bold]{name}[/bold] v{version} [{language}]"
    )


# ===========================================================================
# Shared build helper
# ===========================================================================

def _run_build(
    console: Console,
    cfg: RaikuConfig,
    manifest: dict,
    pkg_dir: Optional[Path],
    name: str,
    trust: bool,
    no_build: bool,
) -> None:
    if no_build:
        console.print(f"  [yellow]⚠[/yellow] Skipping build (--no-build)")
        return

    build_command = manifest.get("build_command", "")
    console.print(f"\n  Build command: [bold yellow]{build_command}[/bold yellow]")

    runner = BuildRunner(safe_mode=cfg.safe_mode, timeout=300)
    tm = TrustManager()
    is_trusted = trust or tm.is_trusted(name) or not cfg.safe_mode

    def confirm_build(cmd: str) -> bool:
        return Confirm.ask(
            f"  Run this build command for [bold]{name}[/bold]?",
            default=False,
        )

    try:
        exit_code = runner.run(
            build_command,
            cwd=pkg_dir,
            package_name=name,
            trusted=is_trusted,
            confirm_callback=confirm_build,
        )
        console.print(f"  [green]✓[/green] Build completed (exit {exit_code})")
    except BuildError as exc:
        console.print(f"  [red]Build error:[/red] {exc}")
        raise click.Abort()
