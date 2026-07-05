"""
raiku search --interactive

A TUI package browser built with rich.live + keyboard input.
Arrow keys scroll, Enter selects, 'i' installs, 'q' quits.

Falls back to a paginated non-interactive display if the terminal
does not support raw input (e.g. CI environments).
"""
from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.align import Align

from core.config import RaikuConfig
from core.constants import SUPPORTED_LANGUAGES, LANGUAGE_ALIASES
from index.index_manager import IndexManager, IndexError


# Colour for the verified badge
VERIFIED_STYLE = "bold green"
VERIFIED_BADGE = "✓ verified"


def _render_table(
    packages: list[dict],
    selected: int,
    query: str,
    status_msg: str = "",
) -> Panel:
    table = Table(
        show_header=True,
        header_style="bold magenta",
        expand=True,
        highlight=False,
    )
    table.add_column("#",         width=4,  style="dim")
    table.add_column("Name",      min_width=20, style="bold")
    table.add_column("Version",   width=10)
    table.add_column("Language",  width=10)
    table.add_column("Tags",      min_width=16, style="dim cyan")
    table.add_column("",          width=12)   # verified badge

    for i, pkg in enumerate(packages):
        tags_str = ", ".join(pkg.get("tags", []))[:30]
        badge    = Text(VERIFIED_BADGE, style=VERIFIED_STYLE) if pkg.get("verified") else Text("")
        row_style = "reverse" if i == selected else ""

        table.add_row(
            str(i + 1),
            pkg.get("name", "—"),
            pkg.get("version", "—"),
            pkg.get("language", "—"),
            tags_str or "—",
            badge,
            style=row_style,
        )

    footer = (
        "[dim]↑↓ navigate  Enter select  i install  q quit[/dim]"
        + (f"  [yellow]{status_msg}[/yellow]" if status_msg else "")
    )
    return Panel(
        table,
        title=f"[bold cyan]Raiku Search[/bold cyan]  [dim]'{query}'[/dim]  "
              f"[dim]({len(packages)} results)[/dim]",
        subtitle=footer,
        border_style="cyan",
    )


def _detail_panel(pkg: dict) -> Panel:
    rows = [
        f"[bold cyan]Name:[/bold cyan]        {pkg.get('name')}",
        f"[bold cyan]Version:[/bold cyan]     {pkg.get('version')}",
        f"[bold cyan]Language:[/bold cyan]    {pkg.get('language')}",
        f"[bold cyan]Author:[/bold cyan]      {pkg.get('author', '—')}",
        f"[bold cyan]Description:[/bold cyan] {pkg.get('description', '—')}",
        f"[bold cyan]Tags:[/bold cyan]        {', '.join(pkg.get('tags', [])) or '—'}",
    ]
    if pkg.get("verified"):
        rows.append(f"[{VERIFIED_STYLE}]✓ Verified package[/{VERIFIED_STYLE}]")
    return Panel("\n".join(rows), title="Package Details", border_style="cyan")


def run_interactive(
    console: Console,
    packages: list[dict],
    query: str,
    cfg: RaikuConfig,
) -> None:
    """Run the interactive TUI browser. Falls back to paginated on non-TTY."""
    if not sys.stdin.isatty():
        _paginated_fallback(console, packages, query)
        return

    try:
        import readchar  # type: ignore
    except ImportError:
        console.print(
            "[yellow]Interactive mode requires the 'readchar' package.[/yellow]\n"
            "Install it: [cyan]pip install readchar[/cyan]\n\n"
            "Falling back to paginated display."
        )
        _paginated_fallback(console, packages, query)
        return

    selected = 0
    status   = ""

    with Live(
        _render_table(packages, selected, query, status),
        console=console,
        screen=False,
        refresh_per_second=20,
    ) as live:
        while True:
            key = readchar.readkey()

            if key in (readchar.key.UP, "k"):
                selected = max(0, selected - 1)
                status = ""

            elif key in (readchar.key.DOWN, "j"):
                selected = min(len(packages) - 1, selected + 1)
                status = ""

            elif key in ("\r", "\n", readchar.key.ENTER):
                live.stop()
                console.print(_detail_panel(packages[selected]))
                live.start()

            elif key.lower() == "i":
                pkg = packages[selected]
                live.stop()
                console.print(
                    f"\n[cyan]Installing [bold]{pkg['name']}[/bold]...[/cyan]"
                )
                import subprocess, sys as _sys
                subprocess.run(
                    [_sys.executable, "-m", "cli.main", "install", pkg["name"]],
                )
                status = f"Installed {pkg['name']}"
                live.start()

            elif key.lower() == "q" or key == readchar.key.CTRL_C:
                break

            live.update(_render_table(packages, selected, query, status))


def _paginated_fallback(
    console: Console,
    packages: list[dict],
    query: str,
    page_size: int = 20,
) -> None:
    """Display packages in pages when interactive mode is unavailable."""
    for i in range(0, len(packages), page_size):
        page = packages[i : i + page_size]
        table = Table(show_header=True, header_style="bold magenta", expand=False)
        table.add_column("Name",     style="bold cyan", min_width=20)
        table.add_column("Version",  style="green", min_width=8)
        table.add_column("Language", style="yellow", min_width=10)
        table.add_column("",         width=12)

        for pkg in page:
            badge = Text(VERIFIED_BADGE, style=VERIFIED_STYLE) if pkg.get("verified") else Text("")
            table.add_row(
                pkg.get("name", "—"),
                pkg.get("version", "—"),
                pkg.get("language", "—"),
                badge,
            )
        console.print(table)

        if i + page_size < len(packages):
            console.print(
                f"[dim]Showing {i+1}–{min(i+page_size, len(packages))} "
                f"of {len(packages)}. Press Enter for more or Ctrl-C to stop.[/dim]"
            )
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                break
