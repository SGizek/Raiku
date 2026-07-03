"""
raiku install <package>

Full install flow:
  1. Load index.json
  2. Find package path
  3. Validate schema compliance
  4. Fetch only the required package files (no full repo clone)
  5. Cache locally at ~/.raiku/cache/
  6. Execute build_command safely (with user confirmation in safe mode)
  7. Confirm installation
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from core.config import RaikuConfig
from core.constants import RAIKU_TOML, VERSION_YML
from index.index_manager import IndexManager, IndexError
from installer.fetcher import PackageFetcher, FetchError
from installer.cache_store import CacheStore
from installer.build_runner import BuildRunner, BuildError
from validator.schema_validator import SchemaValidator, SchemaValidationError
from validator.hash_validator import HashValidator, HashMismatchError
from validator.rules_checker import RulesChecker, RulesViolationError
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError


@click.command("install")
@click.argument("package")
@click.option(
    "--trust", is_flag=True, default=False,
    help="Skip build command confirmation prompt (use with caution).",
)
@click.option(
    "--no-build", is_flag=True, default=False,
    help="Download and cache the package but do not run the build command.",
)
@click.option(
    "--force", "-f", is_flag=True, default=False,
    help="Reinstall even if already cached.",
)
@click.pass_context
def install_cmd(
    ctx: click.Context,
    package: str,
    trust: bool,
    no_build: bool,
    force: bool,
) -> None:
    """Install PACKAGE from the Raiku index."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # ------------------------------------------------------------------ 1. Load index
    console.print(f"[bold cyan]Raiku[/bold cyan] installing [bold]{package}[/bold]...")
    manager = IndexManager(index_url=cfg.index_url)

    try:
        entry = manager.find(package)
    except IndexError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        console.print("Run [cyan]raiku sync[/cyan] first.")
        raise click.Abort()

    if entry is None:
        console.print(
            f"[bold red]Package '{package}' not found.[/bold red] "
            "Run [cyan]raiku search[/cyan] to find available packages."
        )
        raise click.Abort()

    # ------------------------------------------------------------------ 2. Extract metadata
    name: str = entry["name"]
    version: str = entry["version"]
    language: str = entry["language"]
    pkg_path: str = entry["path"]
    expected_sha256: str | None = entry.get("sha256")

    console.print(
        f"  Found: [bold]{name}[/bold] v{version} "
        f"[{language}] by {entry.get('author', 'unknown')}"
    )

    # ------------------------------------------------------------------ Check cache
    store = CacheStore(cfg.cache_dir)
    if store.is_cached(language, name, version) and not force:
        console.print(
            f"[green]✓[/green] Package [bold]{name}[/bold] v{version} "
            "is already installed. Use --force to reinstall."
        )
        return

    # ------------------------------------------------------------------ 3. Fetch files
    fetcher = PackageFetcher(raw_base_url=cfg.raw_base_url)
    files: dict[str, bytes] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Fetching {name}...", total=None)

        try:
            files = fetcher.fetch_package(pkg_path)
        except FetchError as exc:
            console.print(f"[bold red]Fetch error:[/bold red] {exc}")
            raise click.Abort()

        progress.update(task, description=f"Fetched {len(files)} file(s)")

    console.print(f"  [green]✓[/green] Downloaded {len(files)} file(s)")

    # ------------------------------------------------------------------ 4. Validate schema
    schema_v = SchemaValidator()
    hash_v = HashValidator()

    # Parse and validate raiku.toml
    if RAIKU_TOML not in files:
        console.print("[bold red]Error:[/bold red] raiku.toml missing from downloaded files.")
        raise click.Abort()

    try:
        import sys, io
        from pathlib import Path
        import tempfile, os

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for fname, content in files.items():
                dest = tmp_path / fname
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)

            manifest = parse_raiku_toml(tmp_path)
            version_data = parse_version_yml(tmp_path) if VERSION_YML in files else None

            schema_v.validate_raiku_toml(manifest)
            if version_data:
                schema_v.validate_version_yml(version_data)

    except (TomlParseError, YamlParseError, SchemaValidationError) as exc:
        console.print(f"[bold red]Validation error:[/bold red] {exc}")
        raise click.Abort()

    # ------------------------------------------------------------------ Hash check
    toml_bytes = files[RAIKU_TOML]
    try:
        if expected_sha256:
            hash_v.verify_bytes(name, toml_bytes, expected_sha256)
            console.print(f"  [green]✓[/green] Hash verified (sha256)")
        else:
            console.print(
                f"  [yellow]⚠[/yellow] No hash recorded in index — "
                "skipping integrity check"
            )
    except HashMismatchError as exc:
        console.print(f"[bold red]Security alert:[/bold red] {exc}")
        raise click.Abort()

    # ------------------------------------------------------------------ 5. Cache
    store.store_package(language, name, version, files, entry)
    pkg_dir = store.get_package_dir(language, name, version)
    console.print(f"  [green]✓[/green] Cached at: {pkg_dir}")

    # ------------------------------------------------------------------ 6. Build
    if no_build:
        console.print(
            f"  [yellow]⚠[/yellow] Skipping build (--no-build flag set)"
        )
    else:
        build_command = manifest.get("build_command", "")
        console.print(f"\n  Build command: [bold yellow]{build_command}[/bold yellow]")

        runner = BuildRunner(safe_mode=cfg.safe_mode, timeout=300)

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
                trusted=trust or not cfg.safe_mode,
                confirm_callback=confirm_build,
            )
            console.print(f"  [green]✓[/green] Build completed (exit {exit_code})")
        except BuildError as exc:
            console.print(f"[bold red]Build error:[/bold red] {exc}")
            raise click.Abort()

    # ------------------------------------------------------------------ 7. Done
    console.print(
        f"\n[bold green]✓ Installed[/bold green] [bold]{name}[/bold] v{version} [{language}]"
    )
