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
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate and show output without writing any files.")
@click.option("--submit", is_flag=True, default=False,
              help="Automatically open a PR on GitHub (requires raiku login).")
@click.pass_context
def publish_cmd(ctx: click.Context, package_dir: Path, dry_run: bool, submit: bool) -> None:
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
    elif submit:
        _submit_pr(console, name, version, language, target_path, index_entry, package_dir)
    else:
        console.print(
            f"\n[bold green]✓ Package '{name}' v{version} is valid and ready for submission.[/bold green]"
        )


def _submit_pr(
    console: Console,
    name: str,
    version: str,
    language: str,
    target_path: str,
    index_entry: dict,
    package_dir: Path,
) -> None:
    """Open a PR on GitHub using the stored token from raiku login."""
    from cli.commands.login import load_auth, get_token
    import requests, base64, json as _json

    token = get_token()
    if not token:
        console.print(
            "[red]Not logged in.[/red] Run [cyan]raiku login[/cyan] first, "
            "then retry with [cyan]raiku publish --submit[/cyan]."
        )
        raise click.exceptions.Exit(1)

    from core.constants import REPO_OWNER, REPO_NAME

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    auth = load_auth()
    username = auth.get("username", "contributor")
    branch   = f"add/{language.lower()}/{name}"

    console.print(f"  Creating branch [cyan]{branch}[/cyan] ...")

    # 1. Get HEAD sha of main
    resp = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/ref/heads/main",
        headers=headers, timeout=15,
    )
    if not resp.ok:
        console.print(f"[red]Could not read main branch: {resp.status_code} {resp.text}[/red]")
        raise click.exceptions.Exit(1)

    main_sha = resp.json()["object"]["sha"]

    # 2. Create branch
    requests.post(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs",
        headers=headers, timeout=15,
        json={"ref": f"refs/heads/{branch}", "sha": main_sha},
    )

    # 3. Upload each package file
    for fname in ("raiku.toml", "version.yml", "README.md"):
        fpath = package_dir / fname
        if not fpath.exists():
            continue
        content_b64 = base64.b64encode(fpath.read_bytes()).decode()
        api_path = f"{target_path}/{fname}"
        requests.put(
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{api_path}",
            headers=headers, timeout=15,
            json={
                "message": f"add({language}): {name} v{version} — {fname}",
                "content": content_b64,
                "branch": branch,
            },
        )

    console.print(f"  [green]✓[/green] Package files uploaded to branch [cyan]{branch}[/cyan]")

    # 4. Open PR
    pr_body = (
        f"## {name} v{version} [{language}]\n\n"
        f"{index_entry.get('description', '')}\n\n"
        f"**Index entry:**\n```json\n{_json.dumps(index_entry, indent=2)}\n```\n\n"
        f"Submitted via `raiku publish --submit`"
    )
    pr_resp = requests.post(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls",
        headers=headers, timeout=15,
        json={
            "title": f"add({language}): {name} v{version}",
            "head": branch,
            "base": "main",
            "body": pr_body,
        },
    )

    if pr_resp.ok:
        pr_url = pr_resp.json().get("html_url", "")
        console.print(Panel(
            f"[bold green]✓ Pull Request opened![/bold green]\n\n"
            f"  [link={pr_url}]{pr_url}[/link]",
            border_style="green",
        ))
    else:
        console.print(
            f"[yellow]PR could not be opened automatically: "
            f"{pr_resp.status_code} {pr_resp.text}[/yellow]\n"
            "Open it manually at https://github.com/SGizek/Raiku/pulls"
        )
