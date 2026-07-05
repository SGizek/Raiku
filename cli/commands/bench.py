"""
raiku bench <package>

Run the benchmark suite for an installed package.
Auto-detects the benchmark runner based on language:

  Python  → timeit-based (looks for bench_*.py or benchmark*.py in src/)
  Rust    → cargo bench (criterion)
  C/C++   → make bench / cmake --build --target bench
  Zig     → zig build bench
  Java    → mvn exec:java -Dbenchmark  (or JMH if available)
  C#      → dotnet run -c Release --project <bench_proj>
  Go      → go test -bench=. -benchmem ./...
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

_BENCH_RUNNERS: dict[str, list[tuple[str, str, list[str]]]] = {
    "Python": [
        ("python -m timeit", "python",
         ["python", "-m", "pytest", "--benchmark-only", "-v"]),
        ("python bench",     "python",
         ["python", "-m", "timeit", "-n", "1000", "pass"]),
    ],
    "Rust": [
        ("cargo bench", "cargo", ["cargo", "bench"]),
    ],
    "C": [
        ("make bench", "make", ["make", "bench"]),
    ],
    "CPP": [
        ("cmake bench", "cmake",
         ["cmake", "--build", "build", "--target", "bench"]),
        ("make bench", "make", ["make", "bench"]),
    ],
    "Zig": [
        ("zig build bench", "zig", ["zig", "build", "bench"]),
    ],
    "Java": [
        ("mvn benchmark", "mvn",
         ["mvn", "exec:java", "-Dbenchmark=true", "-q"]),
    ],
    "CSharp": [
        ("dotnet bench", "dotnet",
         ["dotnet", "run", "-c", "Release"]),
    ],
    "Go": [
        ("go bench", "go",
         ["go", "test", "-bench=.", "-benchmem", "-run=^$", "./..."]),
    ],
}


@click.command("bench")
@click.argument("package")
@click.option("--version", "pkg_version", default=None,
              help="Specific installed version to benchmark.")
@click.option("--runner", default=None,
              help="Override the benchmark runner command.")
@click.option("--count", "-n", default=None, type=int,
              help="Iteration count (passed to runner where supported).")
@click.pass_context
def bench_cmd(
    ctx: click.Context,
    package: str,
    pkg_version: str | None,
    runner: str | None,
    count: int | None,
) -> None:
    """Run the benchmark suite for an installed PACKAGE."""
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
            f"[red]'{package}' is not installed.[/red] "
            f"Run [cyan]raiku install {package}[/cyan] first."
        )
        raise click.exceptions.Exit(1)

    meta    = sorted(matches, key=lambda m: m.get("version", ""), reverse=True)[0]
    language = meta["language"]
    pkg_dir  = store.get_package_dir(language, meta["name"], meta["version"])

    if pkg_dir is None:
        console.print(f"[red]Cache directory for '{package}' not found.[/red]")
        raise click.exceptions.Exit(1)

    console.print(
        f"[bold cyan]Benchmarking[/bold cyan] [bold]{package}[/bold] "
        f"v{meta['version']} [{language}] in {pkg_dir}\n"
    )

    if runner:
        cmd = runner.split()
        runner_name = runner
    else:
        cmd, runner_name = _select_runner(language, pkg_dir, count)
        if cmd is None:
            console.print(
                f"[yellow]No benchmark runner found for {language}.[/yellow]\n"
                "Install the appropriate toolchain or use [cyan]--runner[/cyan]."
            )
            raise click.exceptions.Exit(1)

    console.print(f"  Runner:  [bold yellow]{runner_name}[/bold yellow]")
    console.print(f"  Command: [dim]{' '.join(cmd)}[/dim]\n")

    result = subprocess.run(cmd, cwd=str(pkg_dir))

    if result.returncode == 0:
        console.print(f"\n[bold green]✓ Benchmarks completed for '{package}'.[/bold green]")
    else:
        console.print(
            f"\n[bold red]✗ Benchmarks failed for '{package}' "
            f"(exit {result.returncode}).[/bold red]"
        )

    raise click.exceptions.Exit(result.returncode)


def _select_runner(
    language: str,
    pkg_dir: Path,
    count: int | None,
) -> tuple[list[str] | None, str]:
    runners = _BENCH_RUNNERS.get(language, [])

    # For Python: look for benchmark files in src/
    if language == "Python":
        src = pkg_dir / "src"
        if src.exists():
            bench_files = list(src.glob("bench_*.py")) + list(src.glob("benchmark*.py"))
            if bench_files and shutil.which("python"):
                cmd = ["python", str(bench_files[0])]
                if count:
                    cmd += [str(count)]
                return cmd, f"python {bench_files[0].name}"

    for name, binary, cmd in runners:
        if shutil.which(binary):
            if count and language in ("Python",):
                cmd = cmd + ["-n", str(count)]
            return list(cmd), name

    return None, ""
