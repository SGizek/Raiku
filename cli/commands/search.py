"""
raiku search <query>

Searches the local index for packages matching the query string.
Optionally filters by language.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from core.config import RaikuConfig
from core.constants import SUPPORTED_LANGUAGES, LANGUAGE_ALIASES
from index.index_manager import IndexManager, IndexError


@click.command("search")
@click.argument("query")
@click.option("--language", "-l", default=None,
              help=f"Filter by language. Supported: {', '.join(SUPPORTED_LANGUAGES)}")
@click.option("--tag", "-t", default=None,
              help="Filter by tag (e.g. math, utils, concurrency).")
@click.option("--sort", default="name",
              type=click.Choice(["name", "latest", "language"], case_sensitive=False),
              help="Sort results by: name (default), latest, language.")
@click.option("--verified", "only_verified", is_flag=True, default=False,
              help="Show only verified packages.")
@click.option("--interactive", "-i", "interactive_mode", is_flag=True, default=False,
              help="Open the interactive TUI package browser.")
@click.option("--limit", "-n", default=20, show_default=True,
              help="Maximum number of results (non-interactive mode).")
@click.pass_context
def search_cmd(
    ctx: click.Context,
    query: str,
    language: str | None,
    tag: str | None,
    sort: str,
    only_verified: bool,
    interactive_mode: bool,
    limit: int,
) -> None:
    """Search the package index for QUERY."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # Normalise language alias
    if language:
        language = LANGUAGE_ALIASES.get(language.lower(), language)
        if language not in SUPPORTED_LANGUAGES:
            console.print(
                f"[yellow]Warning:[/yellow] Unknown language '{language}'. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )

    manager = IndexManager(index_url=cfg.index_url)

    try:
        results = manager.search(query, language=language)
    except IndexError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        console.print("Run [cyan]raiku sync[/cyan] to download the index first.")
        raise click.Abort()

    # Tag filter
    if tag:
        results = [
            r for r in results
            if tag.lower() in [t.lower() for t in r.get("tags", [])]
        ]

    # Sort
    if sort == "latest":
        results = sorted(
            results,
            key=lambda p: str(p.get("release_date", p.get("version", ""))),
            reverse=True,
        )
    elif sort == "language":
        results = sorted(results, key=lambda p: p.get("language", ""))
    else:  # name (default)
        results = sorted(results, key=lambda p: p.get("name", "").lower())

    # Verified filter
    if only_verified:
        results = [r for r in results if r.get("verified")]

    # Interactive mode
    if interactive_mode:
        from cli.commands.interactive import run_interactive
        run_interactive(console, results, query, cfg)
        return

    if not results:
        console.print(
            f"[yellow]No packages found[/yellow] matching "
            f"[bold]'{query}'[/bold]"
            + (f" for language [cyan]{language}[/cyan]" if language else "")
            + (f" with tag [cyan]{tag}[/cyan]" if tag else "")
            + "."
        )
        return

    # Truncate to limit
    shown = results[:limit]
    total = len(results)

    table = Table(
        title=f"Search results for '{query}'"
              + (f" [{language}]" if language else "")
              + (f" #{tag}" if tag else ""),
        show_header=True,
        header_style="bold magenta",
        expand=False,
    )
    table.add_column("Name", style="bold cyan", min_width=20)
    table.add_column("Version", style="green", min_width=8)
    table.add_column("Language", style="yellow", min_width=10)
    table.add_column("Author", style="white", min_width=12)
    table.add_column("Tags", style="dim cyan", min_width=16)
    table.add_column("", width=3)  # verified badge column

    from rich.text import Text as RichText
    for pkg in shown:
        tags_str = ", ".join(pkg.get("tags", []))
        badge = RichText("✓", style="bold green") if pkg.get("verified") else RichText("")
        table.add_row(
            pkg.get("name", "—"),
            pkg.get("version", "—"),
            pkg.get("language", "—"),
            pkg.get("author", "—"),
            tags_str or "—",
            badge,
        )
    console.print(table)

    if total > limit:
        console.print(
            f"[dim]Showing {limit} of {total} results. "
            f"Use --limit to see more.[/dim]"
        )
    else:
        console.print(f"[dim]{total} result(s) found.[/dim]")
