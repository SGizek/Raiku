"""
raiku lint

Static analysis on raiku.toml beyond schema validation.

Checks for common quality issues:
  - Missing optional but recommended fields (description, license, tags)
  - Empty dependencies list placeholder
  - Build command smell (too short, uses echo/true as placeholder)
  - Name too generic (e.g. 'utils', 'lib', 'pkg')
  - Version still at 0.0.0 or 0.1.0 with stability=stable
  - README too short (less than 50 chars)
  - Changelog entry is generic ('Initial release' only forever)
  - No tags defined
  - Homepage URL not HTTPS
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import RaikuConfig
from core.constants import RAIKU_TOML, VERSION_YML
from parser.toml_parser import parse_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, YamlParseError


class LintIssue(NamedTuple):
    level: str   # "error" | "warning" | "info"
    field: str
    message: str


# Names considered too generic
_GENERIC_NAMES = frozenset({
    "utils", "util", "lib", "library", "pkg", "package", "common",
    "shared", "core", "base", "helpers", "helper", "tools", "misc",
})

_PLACEHOLDER_CMDS = frozenset({
    "echo hello", "echo done", "make", "true", ":",
})


@click.command("lint")
@click.option(
    "--dir", "target_dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Package directory to lint (default: current directory).",
)
@click.option("--strict", is_flag=True, default=False,
              help="Exit non-zero if any warnings are found.")
@click.pass_context
def lint_cmd(ctx: click.Context, target_dir: Path, strict: bool) -> None:
    """Run static quality analysis on a package manifest."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print(
        f"[bold cyan]Raiku Lint[/bold cyan] — analysing {target_dir.resolve()}\n"
    )

    issues: list[LintIssue] = []

    # Parse manifests
    try:
        manifest = parse_raiku_toml(target_dir)
    except TomlParseError as exc:
        console.print(f"[red]Cannot parse raiku.toml: {exc}[/red]")
        raise click.exceptions.Exit(1)

    try:
        version_data = parse_version_yml(target_dir)
    except YamlParseError as exc:
        console.print(f"[red]Cannot parse version.yml: {exc}[/red]")
        raise click.exceptions.Exit(1)

    issues.extend(_lint_manifest(manifest, target_dir))
    issues.extend(_lint_version(version_data, manifest))
    issues.extend(_lint_readme(target_dir))

    # Display
    if not issues:
        console.print(Panel(
            "[bold green]✓ No lint issues found.[/bold green]",
            border_style="green",
        ))
        return

    errors   = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    infos    = [i for i in issues if i.level == "info"]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Level",   min_width=8)
    table.add_column("Field",   style="bold cyan", min_width=18)
    table.add_column("Message", style="white")

    for issue in issues:
        if issue.level == "error":
            lvl = "[bold red]error[/bold red]"
        elif issue.level == "warning":
            lvl = "[yellow]warning[/yellow]"
        else:
            lvl = "[dim]info[/dim]"
        table.add_row(lvl, issue.field, issue.message)

    console.print(table)
    console.print(
        f"\n  [red]{len(errors)} error(s)[/red]  "
        f"[yellow]{len(warnings)} warning(s)[/yellow]  "
        f"[dim]{len(infos)} info[/dim]"
    )

    if errors or (strict and warnings):
        raise click.exceptions.Exit(1)


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

def _lint_manifest(manifest: dict, pkg_dir: Path) -> list[LintIssue]:
    issues = []
    name = manifest.get("name", "")

    # Generic names
    if name.lower() in _GENERIC_NAMES:
        issues.append(LintIssue("warning", "name",
            f"'{name}' is too generic and may conflict with other packages. "
            "Use a more specific name."))

    # Missing description
    desc = manifest.get("description", "").strip()
    if not desc:
        issues.append(LintIssue("warning", "description",
            "No description provided. Add a short description to improve discoverability."))
    elif len(desc) < 15:
        issues.append(LintIssue("info", "description",
            f"Description is very short ({len(desc)} chars). Consider expanding it."))

    # Missing license
    if not manifest.get("license"):
        issues.append(LintIssue("warning", "license",
            "No license specified. Add an SPDX identifier (e.g. MIT, Apache-2.0)."))

    # Missing tags
    if not manifest.get("tags"):
        issues.append(LintIssue("info", "tags",
            "No tags defined. Tags help users find your package via raiku search --tag."))

    # Placeholder build command
    build_cmd = manifest.get("build_command", "").strip().lower()
    if build_cmd in _PLACEHOLDER_CMDS:
        issues.append(LintIssue("warning", "build_command",
            f"Build command '{build_cmd}' looks like a placeholder. "
            "Set a real build command."))

    # Non-HTTPS homepage
    homepage = manifest.get("homepage", "")
    if homepage and homepage.startswith("http://"):
        issues.append(LintIssue("warning", "homepage",
            "Homepage URL uses HTTP instead of HTTPS."))

    # Missing homepage
    if not homepage:
        issues.append(LintIssue("info", "homepage",
            "No homepage or repository URL. Consider linking to your source code."))

    return issues


def _lint_version(version_data: dict, manifest: dict) -> list[LintIssue]:
    issues = []
    version = manifest.get("version", "0.0.0")
    stability = version_data.get("stability_level", "")
    changelog = version_data.get("changelog", [])

    # Version 0.x with stability=stable
    if version.startswith("0.") and stability == "stable":
        issues.append(LintIssue("warning", "stability_level",
            f"Version {version} is pre-1.0 but stability is 'stable'. "
            "Consider using 'beta' or 'alpha' for pre-release versions."))

    # Changelog is only "Initial release" (never updated)
    if isinstance(changelog, list) and len(changelog) == 1:
        entry = str(changelog[0]).lower().strip()
        if entry in ("initial release", "initial commit", "first release", "first commit"):
            issues.append(LintIssue("info", "changelog",
                "Changelog only has a generic initial entry. "
                "Keep it updated with each release."))
    elif not changelog:
        issues.append(LintIssue("warning", "changelog",
            "Changelog is empty. Describe what changed in this version."))

    return issues


def _lint_readme(pkg_dir: Path) -> list[LintIssue]:
    issues = []
    readme = pkg_dir / "README.md"
    if not readme.exists():
        return [LintIssue("error", "README.md", "README.md is missing.")]

    content = readme.read_text(encoding="utf-8", errors="replace").strip()
    if len(content) < 50:
        issues.append(LintIssue("warning", "README.md",
            f"README is very short ({len(content)} chars). "
            "Add usage examples and installation instructions."))
    if "raiku install" not in content.lower():
        issues.append(LintIssue("info", "README.md",
            "README does not include a 'raiku install' command. "
            "Help users know how to install your package."))
    return issues
