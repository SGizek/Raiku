"""
raiku why <package>

Explains why a package is installed — was it installed directly by the user,
or is it a dependency of one or more other installed packages?
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from core.config import RaikuConfig
from installer.cache_store import CacheStore
from index.index_manager import IndexManager, IndexError


@click.command("why")
@click.argument("package")
@click.pass_context
def why_cmd(ctx: click.Context, package: str) -> None:
    """Explain why PACKAGE is installed (direct or dependency)."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    store = CacheStore(cfg.cache_dir)
    installed = store.list_installed()
    installed_names = {p.get("name", "").lower() for p in installed}

    target = next(
        (p for p in installed if p.get("name", "").lower() == package.lower()),
        None,
    )

    if target is None:
        console.print(
            f"[yellow]'{package}' is not installed.[/yellow]"
        )
        raise click.exceptions.Exit(1)

    name = target["name"]

    # Try to load index to check which installed packages depend on this one
    try:
        manager = IndexManager(index_url=cfg.index_url)
        manager.load()
        index_available = True
    except IndexError:
        index_available = False

    # Find all installed packages that list this package as a dependency
    dependents: list[str] = []
    if index_available:
        for pkg in installed:
            pkg_name = pkg.get("name", "")
            if pkg_name.lower() == name.lower():
                continue
            entry = manager.find(pkg_name)
            if entry:
                deps = [d.lower() for d in entry.get("dependencies", [])]
                if name.lower() in deps:
                    dependents.append(pkg_name)

    # Build output
    if dependents:
        tree = Tree(f"[bold cyan]{name}[/bold cyan] v{target['version']}")
        dep_branch = tree.add("[dim]required by[/dim]")
        for dep in sorted(dependents):
            dep_entry = manager.find(dep) if index_available else None
            ver = dep_entry.get("version", "?") if dep_entry else "?"
            dep_branch.add(f"[yellow]{dep}[/yellow] v{ver}")
        console.print(
            Panel(tree, title="[bold]Dependency Analysis[/bold]", border_style="cyan")
        )
        console.print(
            f"\n[dim]{name} is a dependency of {len(dependents)} installed package(s).[/dim]"
        )
    else:
        console.print(Panel(
            f"[bold]{name}[/bold] v{target['version']} [{target.get('language', '?')}]\n\n"
            f"[green]Directly installed[/green] — not required by any other installed package.\n"
            f"Safe to remove with [cyan]raiku uninstall {name}[/cyan]",
            title="[bold]Dependency Analysis[/bold]",
            border_style="green",
        ))
        if not index_available:
            console.print("[dim](Run raiku sync to enable full dependency analysis)[/dim]")
