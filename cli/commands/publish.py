"""
raiku publish

Validates the current directory as a Raiku package and prepares
a PR-ready structure (validates schema, checks rules, prints
the diff-ready file listing for the contributor).

Raiku is a community-driven repo — publishing means opening a PR
to add the package under UserSub/<Language>/<package-name>/.
This command prepares and verifies that submission.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import RaikuConfig
from core.constants import RAIKU_TOML, VERSION_YML, README_MD, SRC_DIR, HASH_ALGORITHM
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError
from validator.schema_validator import SchemaValidator, SchemaValidationError
from validator.rules_checker import RulesChecker, RulesViolationError


@click.command("publish")
@click.option(
    "--dir", "package_dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Package directory to publish (default: current directory).",
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Validate and show output without writing any files.",
)
@click.pass_context
def publish_cmd(ctx: click.Context, package_dir: Path, dry_run: bool) -> None:
    """Validate and prepare the current package for contribution (PR submission)."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print(f"[bold cyan]Raiku publish[/bold cyan] — validating {package_dir.resolve()}\n")

    # ------------------------------------------------------------------ Parse manifests
    try:
        manifest = parse_raiku_toml(package_dir)
    except TomlParseError as exc:
        console.print(f"[bold red]raiku.toml error:[/bold red] {exc}")
        raise click.Abort()

    try:
        version_data = parse_version_yml(package_dir)
    except YamlParseError as exc:
        console.print(f"[bold red]version.yml error:[/bold red] {exc}")
        raise click.Abort()

    # ------------------------------------------------------------------ Schema validation
    schema_v = SchemaValidator()
    rules_c = RulesChecker()

    schema_errors: list[str] = []
    rules_errors: list[str] = []

    try:
        schema_v.validate_raiku_toml(manifest)
    except SchemaValidationError as exc:
        schema_errors.extend(
            f"[raiku.toml] {field}: {msg}"
            for field, msgs in exc.errors.items()
            for msg in (msgs if isinstance(msgs, list) else [msgs])
        )

    try:
        schema_v.validate_version_yml(version_data)
    except SchemaValidationError as exc:
        schema_errors.extend(
            f"[version.yml] {field}: {msg}"
            for field, msgs in exc.errors.items()
            for msg in (msgs if isinstance(msgs, list) else [msgs])
        )

    rules_violations = rules_c.check(package_dir, manifest)

    all_errors = schema_errors + rules_violations

    if all_errors:
        console.print(Panel(
            "\n".join(f"  [red]✗[/red] {e}" for e in all_errors),
            title="[bold red]Validation Failed[/bold red]",
            border_style="red",
        ))
        raise click.Abort()

    # ------------------------------------------------------------------ Compute hashes
    name = manifest["name"]
    version = manifest["version"]
    language = manifest["language"]

    toml_bytes = (package_dir / RAIKU_TOML).read_bytes()
    sha256 = hashlib.new(HASH_ALGORITHM, toml_bytes).hexdigest()

    # ------------------------------------------------------------------ Display summary
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Name", name)
    table.add_row("Version", version)
    table.add_row("Language", language)
    table.add_row("Author", manifest.get("author", "—"))
    table.add_row("Build Command", manifest.get("build_command", "—"))
    table.add_row("Stability", version_data.get("stability_level", "—"))
    table.add_row("sha256 (raiku.toml)", sha256)

    console.print(Panel(table, title="[bold green]Package Summary[/bold green]"))

    # ------------------------------------------------------------------ PR instructions
    target_path = f"UserSub/{language}/{name}"

    index_entry = {
        "name": name,
        "version": version,
        "language": language,
        "author": manifest.get("author", ""),
        "description": manifest.get("description", ""),
        "path": target_path,
        "sha256": sha256,
    }

    console.print(Panel(
        f"[bold]Target path in repo:[/bold] [cyan]{target_path}[/cyan]\n\n"
        "[bold]Steps to contribute:[/bold]\n"
        f"  1. Fork [link=https://github.com/SGizek/Raiku]https://github.com/SGizek/Raiku[/link]\n"
        f"  2. Copy your package to [cyan]{target_path}/[/cyan]\n"
        f"  3. Add the following entry to [cyan]index/index.json[/cyan]:\n\n"
        f"[dim]{json.dumps(index_entry, indent=4)}[/dim]\n\n"
        "  4. Open a Pull Request against the [bold]main[/bold] branch",
        title="[bold cyan]Contribution Instructions[/bold cyan]",
    ))

    if dry_run:
        console.print("[dim]Dry run — no files written.[/dim]")
    else:
        console.print(
            f"\n[bold green]✓ Package '{name}' v{version} is valid and ready for submission.[/bold green]"
        )
