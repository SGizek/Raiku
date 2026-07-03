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
@click.option(
    "--language", "-l",
    default=None,
    help=f"Filter by language. Supported: {', '.join(SUPPORTED_LANGUAGES)}",
)
@click.option(
    "--limit", "-n",
    default=20,
    show_default=True,
    help="Maximum number of results to display.",
)
@click.pass_context
def search_cmd(ctx: click.Context, query: str, language: str | None, limit: int) -> None:
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

    if not results:
        console.print(
            f"[yellow]No packages found[/yellow] matching "
            f"[bold]'{query}'[/bold]"
            + (f" for language [cyan]{language}[/cyan]" if language else "")
            + "."
        )
        return

    # Truncate to limit
    shown = results[:limit]
    total = len(results)

    table = Table(
        title=f"Search results for '{query}'" + (f" [{language}]" if language else ""),
        show_header=True,
        header_style="bold magenta",
        expand=False,
    )
    table.add_column("Name", style="bold cyan", min_width=20)
    table.add_column("Version", style="green", min_width=8)
    table.add_column("Language", style="yellow", min_width=10)
    table.add_column("Author", style="white", min_width=15)
    table.add_column("Description", style="dim white", min_width=30)

    for pkg in shown:
        table.add_row(
            pkg.get("name", "—"),
            pkg.get("version", "—"),
            pkg.get("language", "—"),
            pkg.get("author", "—"),
            pkg.get("description", ""),
        )

    console.print(table)

    if total > limit:
        console.print(
            f"[dim]Showing {limit} of {total} results. "
            f"Use --limit to see more.[/dim]"
        )
    else:
        console.print(f"[dim]{total} result(s) found.[/dim]")
