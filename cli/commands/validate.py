"""
raiku validate

Validates one or all packages against schema rules and structural
compliance. Can be run in a single package directory or against
the full UserSub/ tree.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import RaikuConfig
from core.constants import RAIKU_TOML, VERSION_YML, SUPPORTED_LANGUAGES
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError
from validator.schema_validator import SchemaValidator, SchemaValidationError
from validator.rules_checker import RulesChecker


@click.command("validate")
@click.option(
    "--dir", "target_dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory to validate. Defaults to current directory.",
)
@click.option(
    "--all", "validate_all", is_flag=True, default=False,
    help="Validate all packages in UserSub/.",
)
@click.option(
    "--language", "-l", default=None,
    help="When using --all, limit to a specific language.",
)
@click.option(
    "--strict", is_flag=True, default=False,
    help="Exit with non-zero code if any package has warnings.",
)
@click.pass_context
def validate_cmd(
    ctx: click.Context,
    target_dir: Path,
    validate_all: bool,
    language: Optional[str],
    strict: bool,
) -> None:
    """Validate package structure and schema compliance."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if validate_all:
        _validate_all_packages(console, target_dir, language, strict)
    else:
        success = _validate_single(console, target_dir)
        if not success:
            raise click.exceptions.Exit(1)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_single(console: Console, pkg_dir: Path) -> bool:
    """Validate a single package directory. Returns True if fully valid."""
    console.print(f"[bold cyan]Validating:[/bold cyan] {pkg_dir.resolve()}\n")

    schema_v = SchemaValidator()
    rules_c = RulesChecker()

    errors: list[str] = []
    warnings: list[str] = []

    # --- Parse raiku.toml ---
    try:
        manifest = parse_raiku_toml(pkg_dir)
    except TomlParseError as exc:
        errors.append(f"[raiku.toml] Parse error: {exc}")
        manifest = {}

    # --- Parse version.yml ---
    try:
        version_data = parse_version_yml(pkg_dir)
    except YamlParseError as exc:
        errors.append(f"[version.yml] Parse error: {exc}")
        version_data = {}

    # --- Schema validation ---
    if manifest:
        try:
            schema_v.validate_raiku_toml(manifest)
        except SchemaValidationError as exc:
            for field, msgs in exc.errors.items():
                for msg in (msgs if isinstance(msgs, list) else [msgs]):
                    errors.append(f"[raiku.toml:{field}] {msg}")

    if version_data:
        try:
            schema_v.validate_version_yml(version_data)
        except SchemaValidationError as exc:
            for field, msgs in exc.errors.items():
                for msg in (msgs if isinstance(msgs, list) else [msgs]):
                    errors.append(f"[version.yml:{field}] {msg}")

    # --- Rules check ---
    violations = rules_c.check(pkg_dir, manifest)
    errors.extend(violations)

    # --- README check (warning, not error) ---
    if not (pkg_dir / "README.md").exists():
        warnings.append("README.md is missing (recommended but not required)")

    # --- Output ---
    _print_result(console, pkg_dir.name, errors, warnings)

    return len(errors) == 0


def _validate_all_packages(
    console: Console,
    root_dir: Path,
    language: Optional[str],
    strict: bool,
) -> None:
    """Walk UserSub/ and validate every package found."""
    usersub = root_dir / "UserSub"
    if not usersub.exists():
        # Fallback: treat root_dir itself as UserSub
        usersub = root_dir

    languages_to_check = [language] if language else SUPPORTED_LANGUAGES
    results: list[dict] = []

    for lang in languages_to_check:
        lang_dir = usersub / lang
        if not lang_dir.exists():
            continue
        for pkg_dir in sorted(lang_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue
            errors: list[str] = []
            warnings: list[str] = []
            schema_v = SchemaValidator()
            rules_c = RulesChecker()

            try:
                manifest = parse_raiku_toml(pkg_dir)
            except TomlParseError as exc:
                errors.append(str(exc))
                manifest = {}

            try:
                version_data = parse_version_yml(pkg_dir)
            except YamlParseError as exc:
                errors.append(str(exc))
                version_data = {}

            if manifest:
                try:
                    schema_v.validate_raiku_toml(manifest)
                except SchemaValidationError as exc:
                    for field, msgs in exc.errors.items():
                        for msg in (msgs if isinstance(msgs, list) else [msgs]):
                            errors.append(f"{field}: {msg}")

            if version_data:
                try:
                    schema_v.validate_version_yml(version_data)
                except SchemaValidationError as exc:
                    for field, msgs in exc.errors.items():
                        for msg in (msgs if isinstance(msgs, list) else [msgs]):
                            errors.append(f"{field}: {msg}")

            violations = rules_c.check(pkg_dir, manifest)
            errors.extend(violations)

            results.append({
                "name": pkg_dir.name,
                "language": lang,
                "errors": errors,
                "warnings": warnings,
            })

    # --- Summary table ---
    if not results:
        console.print("[yellow]No packages found to validate.[/yellow]")
        return

    table = Table(
        title="Validation Results",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Package", style="bold", min_width=20)
    table.add_column("Language", style="cyan", min_width=10)
    table.add_column("Status", min_width=8)
    table.add_column("Issues", style="dim")

    total_errors = 0
    for r in results:
        if r["errors"]:
            status = "[bold red]FAIL[/bold red]"
            issues = f"{len(r['errors'])} error(s)"
            total_errors += 1
        elif r["warnings"]:
            status = "[yellow]WARN[/yellow]"
            issues = f"{len(r['warnings'])} warning(s)"
        else:
            status = "[green]PASS[/green]"
            issues = "—"
        table.add_row(r["name"], r["language"], status, issues)

    console.print(table)

    if total_errors > 0:
        console.print(
            f"\n[bold red]{total_errors}[/bold red] package(s) failed validation."
        )
        # Print details for failing packages
        for r in results:
            if r["errors"]:
                console.print(f"\n[bold red]{r['name']}[/bold red] [{r['language']}]:")
                for err in r["errors"]:
                    console.print(f"  [red]✗[/red] {err}")
        if strict:
            raise click.exceptions.Exit(1)
    else:
        console.print(
            f"\n[bold green]✓ All {len(results)} package(s) passed validation.[/bold green]"
        )


def _print_result(
    console: Console,
    name: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    if errors:
        console.print(Panel(
            "\n".join(f"  [red]✗[/red] {e}" for e in errors),
            title=f"[bold red]FAILED[/bold red]: {name}",
            border_style="red",
        ))
    else:
        lines = [f"[green]✓[/green] All checks passed for [bold]{name}[/bold]"]
        if warnings:
            lines.append("")
            for w in warnings:
                lines.append(f"  [yellow]⚠[/yellow] {w}")
        console.print(Panel(
            "\n".join(lines),
            title="[bold green]PASSED[/bold green]",
            border_style="green",
        ))
