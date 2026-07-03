"""
Raiku CLI — entry point.

Registers all subcommands and initialises the shared Click context.
"""
from __future__ import annotations

import click
from rich.console import Console

from core.config import RaikuConfig
from core.constants import VERSION, CLI_NAME

console = Console()


@click.group()
@click.version_option(version=VERSION, prog_name=CLI_NAME)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose output.")
@click.option("--no-color", is_flag=True, default=False, help="Disable colored output.")
@click.pass_context
def main(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """
    Raiku — community-driven, Git-based, multi-language package manager.

    \b
    Quick start:
      raiku sync                  # Update local index
      raiku search <query>        # Find packages
      raiku install <package>     # Install a package
      raiku publish               # Publish your package
      raiku validate              # Validate package structure
    """
    ctx.ensure_object(dict)
    cfg = RaikuConfig.load()
    if verbose:
        cfg.verbose = True
    if no_color:
        cfg.color = False
    cfg.ensure_dirs()
    ctx.obj["config"] = cfg
    ctx.obj["console"] = Console(highlight=cfg.color)


# Register subcommands
from cli.commands.sync import sync_cmd
from cli.commands.search import search_cmd
from cli.commands.install import install_cmd
from cli.commands.publish import publish_cmd
from cli.commands.validate import validate_cmd

main.add_command(sync_cmd, name="sync")
main.add_command(search_cmd, name="search")
main.add_command(install_cmd, name="install")
main.add_command(publish_cmd, name="publish")
main.add_command(validate_cmd, name="validate")


if __name__ == "__main__":
    main()
