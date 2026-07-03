"""
raiku doctor

Checks that all required build tools are installed and accessible,
reports versions, and flags anything missing.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from core.config import RaikuConfig


@dataclass
class Tool:
    name: str
    command: str
    version_flag: str
    language: str
    required: bool = True
    install_hint: str = ""


TOOLS: list[Tool] = [
    Tool("Python",    "python",   "--version",  "Python",  True,
         "https://python.org"),
    Tool("pip",       "pip",      "--version",  "Python",  True,
         "Bundled with Python — run: python -m ensurepip"),
    Tool("GCC",       "gcc",      "--version",  "C/C++",   False,
         "https://gcc.gnu.org / apt install gcc"),
    Tool("Clang",     "clang",    "--version",  "C/C++",   False,
         "https://clang.llvm.org"),
    Tool("CMake",     "cmake",    "--version",  "C++",     False,
         "https://cmake.org / pip install cmake"),
    Tool("Cargo",     "cargo",    "--version",  "Rust",    False,
         "https://rustup.rs"),
    Tool("Zig",       "zig",      "version",    "Zig",     False,
         "https://ziglang.org/download"),
    Tool("Java (javac)", "javac", "-version",   "Java",    False,
         "https://adoptium.net"),
    Tool("Go",        "go",       "version",    "Go",      False,
         "https://go.dev/dl"),
    Tool("dotnet",    "dotnet",   "--version",  "C#",      False,
         "https://dotnet.microsoft.com/download"),
    Tool("git",       "git",      "--version",  "General", True,
         "https://git-scm.com"),
]


def _probe(tool: Tool) -> tuple[bool, Optional[str]]:
    """Return (found, version_string)."""
    if shutil.which(tool.command) is None:
        return False, None
    try:
        result = subprocess.run(
            [tool.command, tool.version_flag],
            capture_output=True, text=True, timeout=5,
        )
        output = (result.stdout + result.stderr).strip()
        # Grab first line only
        version = output.splitlines()[0] if output else "?"
        return True, version
    except Exception:
        return False, None


@click.command("doctor")
@click.option("--language", "-l", default=None,
              help="Only check tools for a specific language.")
@click.pass_context
def doctor_cmd(ctx: click.Context, language: str | None) -> None:
    """Check that all required build tools are installed."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("[bold cyan]Raiku Doctor[/bold cyan] — checking build tools\n")

    tools = TOOLS
    if language:
        tools = [t for t in tools
                 if t.language.lower() == language.lower()
                 or t.language == "General"]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool",      style="bold", min_width=16)
    table.add_column("Language",  style="cyan",  min_width=10)
    table.add_column("Status",    min_width=8)
    table.add_column("Version / Info", style="dim", min_width=40)

    missing_required: list[Tool] = []
    missing_optional: list[Tool] = []

    for tool in tools:
        found, version = _probe(tool)

        if found:
            status = "[bold green]✓ found[/bold green]"
            info = version or "—"
        elif tool.required:
            status = "[bold red]✗ MISSING[/bold red]"
            info = f"[red]Install: {tool.install_hint}[/red]"
            missing_required.append(tool)
        else:
            status = "[yellow]– optional[/yellow]"
            info = f"[dim]Install: {tool.install_hint}[/dim]"
            missing_optional.append(tool)

        table.add_row(tool.name, tool.language, status, info)

    console.print(table)

    if missing_required:
        console.print(
            f"\n[bold red]✗ {len(missing_required)} required tool(s) missing.[/bold red] "
            "Raiku may not function correctly."
        )
    elif missing_optional:
        console.print(
            f"\n[yellow]{len(missing_optional)} optional tool(s) not found.[/yellow] "
            "Only packages needing those languages will be affected."
        )
    else:
        console.print("\n[bold green]✓ All tools present. Raiku is fully operational.[/bold green]")

    # Raiku-specific checks
    console.print()
    _check_raiku_home(console, cfg)


def _check_raiku_home(console: Console, cfg: RaikuConfig) -> None:
    from core.constants import INDEX_CACHE_PATH
    checks = [
        ("~/.raiku/ exists",         cfg.cache_dir.parent.exists()),
        ("Cache directory exists",   cfg.cache_dir.exists()),
        ("Index cached",             INDEX_CACHE_PATH.exists()),
    ]
    for label, ok in checks:
        icon = "[green]✓[/green]" if ok else "[yellow]–[/yellow]"
        console.print(f"  {icon} {label}")
