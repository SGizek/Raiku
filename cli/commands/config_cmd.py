"""
raiku config

View and set Raiku configuration values without manually editing
~/.raiku/config.toml.

    raiku config list
    raiku config get safe_mode
    raiku config set safe_mode false
    raiku config reset
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config import RaikuConfig


# All user-settable keys and their types
_SETTINGS: dict[str, tuple[type, str]] = {
    "safe_mode":      (bool,  "Always prompt before running build commands"),
    "auto_trust":     (bool,  "Never silently trust packages (keep false)"),
    "verbose":        (bool,  "Enable verbose output by default"),
    "color":          (bool,  "Enable colored CLI output"),
    "index_url":      (str,   "URL of the remote index.json"),
    "raw_base_url":   (str,   "Base URL for raw package file fetching"),
}


@click.group("config")
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    """View and modify Raiku configuration."""
    pass


@config_cmd.command("list")
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """Show all current configuration values."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Key",         style="bold cyan", min_width=18)
    table.add_column("Value",       style="green",     min_width=10)
    table.add_column("Description", style="dim")

    for key, (typ, desc) in _SETTINGS.items():
        val = getattr(cfg, key, "—")
        table.add_row(key, str(val), desc)

    console.print(Panel(
        table,
        title=f"Raiku Configuration  [dim]({cfg.config_path})[/dim]",
    ))


@config_cmd.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """Print the value of a single config KEY."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if key not in _SETTINGS:
        console.print(
            f"[red]Unknown key '{key}'.[/red] "
            f"Valid keys: {', '.join(_SETTINGS)}"
        )
        raise click.exceptions.Exit(1)

    val = getattr(cfg, key, None)
    console.print(f"{key} = {val}")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set config KEY to VALUE and save to disk."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if key not in _SETTINGS:
        console.print(
            f"[red]Unknown key '{key}'.[/red] "
            f"Valid keys: {', '.join(_SETTINGS)}"
        )
        raise click.exceptions.Exit(1)

    typ, _ = _SETTINGS[key]

    # Type coercion
    try:
        if typ is bool:
            if value.lower() in ("true", "1", "yes", "on"):
                coerced = True
            elif value.lower() in ("false", "0", "no", "off"):
                coerced = False
            else:
                raise ValueError(f"Expected true/false, got '{value}'")
        else:
            coerced = typ(value)
    except ValueError as exc:
        console.print(f"[red]Invalid value:[/red] {exc}")
        raise click.exceptions.Exit(1)

    # Security warning for dangerous settings
    if key == "auto_trust" and coerced is True:
        console.print(
            "[yellow]Warning:[/yellow] Enabling auto_trust means build commands "
            "will run without confirmation. Only do this in trusted environments."
        )
    if key == "safe_mode" and coerced is False:
        console.print(
            "[yellow]Warning:[/yellow] Disabling safe_mode means build commands "
            "will execute without prompting you first."
        )

    setattr(cfg, key, coerced)
    cfg.save()
    console.print(f"[green]✓[/green] {key} = {coerced}  (saved to {cfg.config_path})")


@config_cmd.command("reset")
@click.option("--yes", "-y", is_flag=True, default=False)
@click.pass_context
def config_reset(ctx: click.Context, yes: bool) -> None:
    """Reset all configuration to defaults."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if not yes:
        from rich.prompt import Confirm
        if not Confirm.ask("Reset all config to defaults?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    defaults = RaikuConfig()
    defaults.save()
    console.print(f"[green]✓[/green] Configuration reset to defaults. ({cfg.config_path})")
