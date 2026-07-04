"""
raiku graph

Print an ASCII dependency graph of all installed packages.
Shows which packages depend on which, and flags missing dependencies.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel

from core.config import RaikuConfig
from installer.cache_store import CacheStore
from index.index_manager import IndexManager, IndexError


@click.command("graph")
@click.option("--package", "-p", default=None,
              help="Show graph for a single package only.")
@click.option("--language", "-l", default=None,
              help="Filter to one language.")
@click.pass_context
def graph_cmd(
    ctx: click.Context,
    package: str | None,
    language: str | None,
) -> None:
    """Print a dependency graph of installed packages."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    installed = store.list_installed()

    if not installed:
        console.print("[yellow]No packages installed.[/yellow]")
        return

    if language:
        installed = [p for p in installed if p.get("language", "").lower() == language.lower()]

    if package:
        installed = [p for p in installed if p.get("name", "").lower() == package.lower()]
        if not installed:
            console.print(f"[red]'{package}' is not installed.[/red]")
            raise click.exceptions.Exit(1)

    # Try to load index for dep metadata
    try:
        manager = IndexManager(index_url=cfg.index_url)
        manager.load()
        index_ok = True
    except IndexError:
        index_ok = False
        console.print("[dim]Index not loaded — dependency edges not shown. Run raiku sync.[/dim]\n")

    installed_map = {p.get("name", "").lower(): p for p in installed}

    # Build trees — only show root packages (not depended-upon by others)
    # if showing all packages
    depended_upon: set[str] = set()
    if index_ok:
        for pkg in installed:
            entry = manager.find(pkg.get("name", ""))
            if entry:
                for dep in entry.get("dependencies", []):
                    depended_upon.add(dep.lower())

    roots = installed if package else [
        p for p in installed
        if p.get("name", "").lower() not in depended_upon
    ]

    # Also include packages with no index entry at roots
    if not package:
        for pkg in installed:
            if pkg.get("name", "").lower() not in depended_upon:
                if pkg not in roots:
                    roots.append(pkg)

    trees = []
    visited: set[str] = set()

    def build_tree(name: str, tree_node: Tree, depth: int = 0) -> None:
        if depth > 10:
            tree_node.add("[dim]... (max depth)[/dim]")
            return
        entry = manager.find(name) if index_ok else None
        deps = entry.get("dependencies", []) if entry else []
        for dep in deps:
            dep_lower = dep.lower()
            if dep_lower in installed_map:
                meta = installed_map[dep_lower]
                node = tree_node.add(
                    f"[cyan]{dep}[/cyan] v{meta.get('version', '?')} "
                    f"[dim][{meta.get('language', '?')}][/dim]"
                )
                if dep_lower not in visited:
                    visited.add(dep_lower)
                    build_tree(dep, node, depth + 1)
            else:
                tree_node.add(f"[yellow]{dep}[/yellow] [dim](not installed)[/dim]")

    for pkg in sorted(roots, key=lambda p: p.get("name", "")):
        name = pkg.get("name", "?")
        ver  = pkg.get("version", "?")
        lang = pkg.get("language", "?")
        root_tree = Tree(
            f"[bold green]{name}[/bold green] v{ver} [dim][{lang}][/dim]"
        )
        visited.add(name.lower())
        build_tree(name, root_tree)
        trees.append(root_tree)

    console.print(Panel(
        "\n".join(str(t) for t in trees) if trees else "[dim]No packages to show.[/dim]",
        title="[bold]Dependency Graph[/bold]",
        border_style="cyan",
    ))

    total = len(installed)
    console.print(f"[dim]{total} package(s) installed.[/dim]")
