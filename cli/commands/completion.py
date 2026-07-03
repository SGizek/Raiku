"""
raiku completion

Generates shell completion scripts for bash, zsh, fish, and PowerShell.

Usage:
    raiku completion bash   >> ~/.bashrc
    raiku completion zsh    >> ~/.zshrc
    raiku completion fish   > ~/.config/fish/completions/raiku.fish
    raiku completion powershell >> $PROFILE

Or use the auto-install flag:
    raiku completion bash --install
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from core.config import RaikuConfig

SUPPORTED_SHELLS = ("bash", "zsh", "fish", "powershell")


@click.command("completion")
@click.argument("shell", type=click.Choice(SUPPORTED_SHELLS, case_sensitive=False))
@click.option("--install", is_flag=True, default=False,
              help="Automatically append the completion script to your shell config.")
@click.pass_context
def completion_cmd(ctx: click.Context, shell: str, install: bool) -> None:
    """Generate shell completion scripts."""
    cfg: RaikuConfig = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    shell = shell.lower()

    # Click has built-in completion support via env vars
    # We generate the eval snippet the user needs to add to their shell config
    script, config_file = _generate(shell)

    if install:
        _auto_install(console, shell, script, config_file)
        return

    console.print(Panel(
        Syntax(script, "bash" if shell != "fish" else "fish", theme="monokai"),
        title=f"[bold]Completion script for {shell}[/bold]",
        subtitle=f"[dim]Add this to {config_file}[/dim]",
    ))
    console.print()
    console.print(f"To install automatically: [cyan]raiku completion {shell} --install[/cyan]")
    console.print(f"Or manually append to [cyan]{config_file}[/cyan]")


def _generate(shell: str) -> tuple[str, str]:
    """Return (script_content, config_file_path)."""
    prog = "raiku"

    if shell == "bash":
        script = f'eval "$(_RAIKU_COMPLETE=bash_source {prog})"'
        config = "~/.bashrc"

    elif shell == "zsh":
        script = f'eval "$(_RAIKU_COMPLETE=zsh_source {prog})"'
        config = "~/.zshrc"

    elif shell == "fish":
        script = f"_RAIKU_COMPLETE=fish_source {prog} | source"
        config = "~/.config/fish/completions/raiku.fish"

    elif shell == "powershell":
        script = (
            f'$env:_RAIKU_COMPLETE = "powershell_source"\n'
            f'& {prog} | Invoke-Expression\n'
            f'Remove-Item Env:_RAIKU_COMPLETE'
        )
        config = "$PROFILE"

    else:
        script = ""
        config = ""

    return script, config


def _auto_install(console: Console, shell: str, script: str, config_file: str) -> None:
    """Append the completion script to the user's shell config."""
    expanded = Path(config_file.replace("$PROFILE", _powershell_profile())).expanduser()

    # Fish writes to its own completions dir — create the file directly
    if shell == "fish":
        expanded.parent.mkdir(parents=True, exist_ok=True)
        expanded.write_text(script + "\n", encoding="utf-8")
        console.print(f"[green]✓[/green] Fish completion written to [cyan]{expanded}[/cyan]")
        return

    # For others, append if not already present
    marker = "# raiku completion"
    block = f"\n{marker}\n{script}\n"

    if expanded.exists():
        existing = expanded.read_text(encoding="utf-8")
        if marker in existing:
            console.print(
                f"[yellow]Completion already installed[/yellow] in [cyan]{expanded}[/cyan]"
            )
            return

    with open(expanded, "a", encoding="utf-8") as f:
        f.write(block)

    console.print(f"[green]✓[/green] Completion installed to [cyan]{expanded}[/cyan]")
    console.print(f"  Restart your shell or run: [cyan]source {config_file}[/cyan]")


def _powershell_profile() -> str:
    """Get the current PowerShell profile path."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "echo $PROFILE"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or "~/Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
    except Exception:
        return "~/Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
