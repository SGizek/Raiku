"""
raiku test <package>

Run the test suite of an installed package from its cache directory.
Auto-detects the test runner based on language:

  Python  → pytest (fallback: python -m unittest discover)
  Rust    → cargo test
  C       → make test  (fallback: run a *_test binary if found)
  C++     → cmake --build build --target test  (fallback: ctest)
  Zig     → zig build test
  Java    → mvn test (fallback: javac + java on *Test.java files)
  C#      → dotnet test
  Go      → go test ./...
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from core.config import RaikuConfig
from installer.cache_store import CacheStore


# Language → ordered list of (display_name, check_command, test_command)
# check_command is the binary to look for with shutil.which
_TEST_RUNNERS: dict[str, list[tuple[str, str, list[str]]]] = {
    "Python": [
        ("pytest",   "pytest",  ["pytest", "-v"]),
        ("unittest", "python",  ["python", "-m", "unittest", "discover", "-v"]),
    ],
    "Rust": [
        ("cargo test", "cargo", ["cargo", "test"]),
    ],
    "C": [
        ("make test", "make",  ["make", "test"]),
    ],
    "CPP": [
        ("ctest",  "ctest",  ["cmake", "--build", "build", "--target", "test"]),
        ("cmake",  "cmake",  ["ctest", "--test-dir", "build", "-V"]),
    ],
    "Zig": [
        ("zig build test", "zig", ["zig", "build", "test"]),
    ],
    "Java": [
        ("mvn",   "mvn",   ["mvn", "test", "-q"]),
        ("gradle","gradle",["gradle", "test"]),
    ],
    "CSharp": [
        ("dotnet test", "dotnet", ["dotnet", "test"]),
    ],
    "Go": [
        ("go test", "go", ["go", "test", "./..."]),
    ],
}


@click.command("test")
@click.argument("package")
@click.option("--version", "pkg_version", default=None,
              help="Specific installed version to test.")
@click.option("--runner", default=None,
              help="Override the test runner command (e.g. 'pytest').")
@click.pass_context
def test_cmd(
    ctx: click.Context,
    package: str,
    pkg_version: str | None,
    runner: str | None,
) -> None:
    """Run the test suite of an installed PACKAGE."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

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

    meta = sorted(matches, key=lambda m: m.get("version", ""), reverse=True)[0]
    language = meta["language"]
    pkg_dir  = store.get_package_dir(language, meta["name"], meta["version"])

    if pkg_dir is None:
        console.print(f"[red]Cache directory for '{package}' not found.[/red]")
        raise click.exceptions.Exit(1)

    console.print(
        f"[bold cyan]Testing[/bold cyan] [bold]{package}[/bold] "
        f"v{meta['version']} [{language}] in {pkg_dir}\n"
    )

    # --- Select test command ---
    if runner:
        cmd = runner.split()
        runner_name = runner
    else:
        cmd, runner_name = _select_runner(language, pkg_dir)
        if cmd is None:
            console.print(
                f"[yellow]No test runner found for {language}.[/yellow]\n"
                "Install the appropriate tool or use [cyan]--runner[/cyan] to specify one."
            )
            raise click.exceptions.Exit(1)

    console.print(f"  Runner: [bold yellow]{runner_name}[/bold yellow]")
    console.print(f"  Command: [dim]{' '.join(cmd)}[/dim]\n")

    result = subprocess.run(cmd, cwd=str(pkg_dir))

    if result.returncode == 0:
        console.print(f"\n[bold green]✓ Tests passed for '{package}'.[/bold green]")
    else:
        console.print(
            f"\n[bold red]✗ Tests failed for '{package}' "
            f"(exit {result.returncode}).[/bold red]"
        )

    raise click.exceptions.Exit(result.returncode)


def _select_runner(
    language: str,
    pkg_dir: Path,
) -> tuple[list[str] | None, str]:
    """Return (command_list, display_name) for the first available runner."""
    runners = _TEST_RUNNERS.get(language, [])
    for name, binary, cmd in runners:
        if shutil.which(binary):
            return cmd, name
    return None, ""
