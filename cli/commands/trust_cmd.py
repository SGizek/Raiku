"""
raiku trust

Manage the local trusted-packages list.

    raiku trust add <package> [--reason "..."]
    raiku trust remove <package>
    raiku trust list
    raiku trust clear
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from core.config import RaikuConfig
from core.trust import TrustManager


@click.group("trust")
@click.pass_context
def trust_cmd(ctx: click.Context) -> None:
    """Manage the local trusted-packages list."""
    pass


@trust_cmd.command("add")
@click.argument("package")
@click.option("--reason", default="", help="Optional note explaining why this package is trusted.")
@click.pass_context
def trust_add(ctx: click.Context, package: str, reason: str) -> None:
    """Mark PACKAGE as trusted (skips build-command confirmation on install)."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    tm = TrustManager()

    if tm.is_trusted(package):
        console.print(f"[yellow]'{package}' is already trusted.[/yellow]")
        return

    console.print(
        f"  [yellow]Warning:[/yellow] Trusting [bold]{package}[/bold] means its "
        "build command will run without prompting you for confirmation."
    )

    confirmed = Confirm.ask(f"Trust '{package}'?", default=False)
    if not confirmed:
        console.print("[dim]Aborted.[/dim]")
        return

    tm.add(package, reason=reason)
    console.print(f"[green]✓[/green] '{package}' added to trusted list.")


@trust_cmd.command("remove")
@click.argument("package")
@click.pass_context
def trust_remove(ctx: click.Context, package: str) -> None:
    """Remove PACKAGE from the trusted list."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    tm = TrustManager()
    removed = tm.remove(package)

    if removed:
        console.print(f"[green]✓[/green] '{package}' removed from trusted list.")
    else:
        console.print(f"[yellow]'{package}' was not in the trusted list.[/yellow]")


@trust_cmd.command("list")
@click.pass_context
def trust_list(ctx: click.Context) -> None:
    """Show all currently trusted packages."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    tm = TrustManager()
    trusted = tm.list_trusted()

    if not trusted:
        console.print("[dim]No packages are currently trusted.[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="bold cyan")
    table.add_column("Trusted Since", style="green")
    table.add_column("Reason", style="dim")

    for entry in sorted(trusted, key=lambda e: e.get("name", "")):
        import datetime
        ts = entry.get("trusted_at")
        dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "—"
        table.add_row(
            entry.get("name", "—"),
            dt,
            entry.get("reason", "—") or "—",
        )

    console.print(table)
    console.print(f"[dim]{len(trusted)} trusted package(s).[/dim]")


@trust_cmd.command("clear")
@click.option("--yes", "-y", is_flag=True, default=False)
@click.pass_context
def trust_clear(ctx: click.Context, yes: bool) -> None:
    """Remove ALL packages from the trusted list."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    tm = TrustManager()
    if not tm.list_trusted():
        console.print("[dim]Trusted list is already empty.[/dim]")
        return

    if not yes:
        if not Confirm.ask("Remove all trusted packages?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    count = tm.clear()
    console.print(f"[green]✓[/green] Cleared {count} trusted package(s).")
