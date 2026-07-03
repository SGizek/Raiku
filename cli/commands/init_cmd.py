"""
raiku init

Interactive wizard that scaffolds a new Raiku package in the current
(or specified) directory. Generates:

    <name>/
      raiku.toml
      version.yml
      README.md
      src/         (language-specific source files)
"""
from __future__ import annotations

import re
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from core.config import RaikuConfig
from core.constants import SUPPORTED_LANGUAGES, STABILITY_LEVELS
from core.templates import TEMPLATES, get_template, expand_filename


_NAME_RE = re.compile(r"^[a-z][a-z0-9_\-]*$")


@click.command("init")
@click.argument("name", required=False, default=None)
@click.option("--language", "-l", default=None,
              help="Package language (skips prompt).")
@click.option("--output-dir", "-o", default=".",
              type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
              help="Directory to create the package in (default: current dir).")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Accept all defaults without prompting.")
@click.pass_context
def init_cmd(
    ctx: click.Context,
    name: str | None,
    language: str | None,
    output_dir: Path,
    yes: bool,
) -> None:
    """Scaffold a new Raiku package interactively."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print(Panel(
        "[bold cyan]Raiku Package Wizard[/bold cyan]\n"
        "[dim]Creates a new package with all required files.[/dim]",
        border_style="cyan",
    ))

    # ------------------------------------------------------------------ Name
    if name is None:
        name = Prompt.ask("  Package name", default="my-package")

    name = name.strip().lower()
    if not _NAME_RE.match(name):
        console.print(
            "[red]Invalid name.[/red] Use lowercase letters, digits, hyphens, underscores. "
            "Must start with a letter."
        )
        raise click.exceptions.Exit(1)

    # ------------------------------------------------------------------ Language
    lang_list = ", ".join(SUPPORTED_LANGUAGES)
    if language is None:
        language = Prompt.ask(f"  Language [{lang_list}]", default="Python")

    language = language.strip()
    # Normalise aliases
    from core.constants import LANGUAGE_ALIASES
    language = LANGUAGE_ALIASES.get(language.lower(), language)

    if language not in SUPPORTED_LANGUAGES:
        console.print(f"[red]Unknown language '{language}'.[/red] Choose from: {lang_list}")
        raise click.exceptions.Exit(1)

    # ------------------------------------------------------------------ Other fields
    version   = Prompt.ask("  Version",     default="1.0.0")        if not yes else "1.0.0"
    author    = Prompt.ask("  Author",      default="Your Name")    if not yes else "Your Name"
    desc      = Prompt.ask("  Description", default="")             if not yes else ""
    license_  = Prompt.ask("  License",     default="MIT")          if not yes else "MIT"
    stability = Prompt.ask(
        f"  Stability [{'/'.join(STABILITY_LEVELS)}]", default="stable"
    ) if not yes else "stable"

    template = get_template(language)
    build_cmd = template.default_build_command if template else "make"
    # Expand {name} in default build command
    name_safe = name.replace("-", "_")
    build_cmd = build_cmd.replace("{name}", name).replace("{name_safe}", name_safe)

    if not yes:
        custom_build = Prompt.ask("  Build command", default=build_cmd)
        build_cmd = custom_build.strip() or build_cmd

    # ------------------------------------------------------------------ Tags
    tags_raw = Prompt.ask("  Tags (comma-separated)", default="") if not yes else ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    # ------------------------------------------------------------------ Confirm
    console.print()
    console.print(f"  [bold]Name:[/bold]          {name}")
    console.print(f"  [bold]Language:[/bold]      {language}")
    console.print(f"  [bold]Version:[/bold]       {version}")
    console.print(f"  [bold]Author:[/bold]        {author}")
    console.print(f"  [bold]Description:[/bold]   {desc or '—'}")
    console.print(f"  [bold]Build command:[/bold] {build_cmd}")
    console.print(f"  [bold]Tags:[/bold]          {', '.join(tags) or '—'}")
    console.print()

    if not yes:
        if not Confirm.ask("  Create package?", default=True):
            console.print("[dim]Aborted.[/dim]")
            return

    # ------------------------------------------------------------------ Build context
    cls = "".join(w.capitalize() for w in name_safe.split("_"))
    ctx_data = {
        "name": name,
        "name_safe": name_safe,
        "cls": cls,
        "version": version,
        "author": author,
        "description": desc,
        "license": license_,
    }

    # ------------------------------------------------------------------ Create files
    pkg_dir = output_dir / name
    if pkg_dir.exists():
        console.print(f"[red]Directory '{pkg_dir}' already exists.[/red]")
        raise click.exceptions.Exit(1)

    pkg_dir.mkdir(parents=True)
    src_dir = pkg_dir / "src"
    src_dir.mkdir()

    # raiku.toml
    import tomli_w
    toml_data: dict = {
        "name": name,
        "version": version,
        "language": language,
        "author": author,
        "build_command": build_cmd,
    }
    if desc:
        toml_data["description"] = desc
    if license_:
        toml_data["license"] = license_
    if tags:
        toml_data["tags"] = tags

    with open(pkg_dir / "raiku.toml", "wb") as f:
        tomli_w.dump(toml_data, f)

    # version.yml
    import yaml, datetime
    yml_data = {
        "version": version,
        "release_date": datetime.date.today().isoformat(),
        "stability_level": stability,
        "changelog": ["Initial release"],
    }
    with open(pkg_dir / "version.yml", "w", encoding="utf-8") as f:
        yaml.dump(yml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # README.md
    readme = f"""# {name}

{desc or 'A Raiku package.'}

## Installation

```bash
raiku install {name}
```

## Usage

TODO: add usage examples.

## License

{license_}
"""
    (pkg_dir / "README.md").write_text(readme, encoding="utf-8")

    # Source files from template
    if template:
        for tmpl_file in template.src_files:
            fname = expand_filename(tmpl_file.filename, ctx_data)
            fpath = src_dir / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(tmpl_file.content_fn(ctx_data), encoding="utf-8")
            console.print(f"  [green]✓[/green] src/{fname}")

        for tmpl_file in template.extra_root_files:
            fname = expand_filename(tmpl_file.filename, ctx_data)
            fpath = pkg_dir / fname
            fpath.write_text(tmpl_file.content_fn(ctx_data), encoding="utf-8")
            console.print(f"  [green]✓[/green] {fname}")

    console.print(f"  [green]✓[/green] raiku.toml")
    console.print(f"  [green]✓[/green] version.yml")
    console.print(f"  [green]✓[/green] README.md")

    console.print(Panel(
        f"[bold green]✓ Package '{name}' created at {pkg_dir}[/bold green]\n\n"
        f"Next steps:\n"
        f"  1. Add your source code to [cyan]{pkg_dir}/src/[/cyan]\n"
        f"  2. Run [cyan]raiku validate --dir {pkg_dir}[/cyan] to check it\n"
        f"  3. Run [cyan]raiku publish --dir {pkg_dir}[/cyan] to prepare a PR",
        border_style="green",
    ))
