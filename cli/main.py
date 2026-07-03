"""
Raiku CLI — entry point.

Registers all subcommands and initialises the shared Click context.
"""
from __future__ import annotations

import click
from rich.console import Console

from core.config import RaikuConfig
from core.constants import VERSION, CLI_NAME


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
      raiku sync                    # Update local index
      raiku search <query>          # Find packages
      raiku install <package>       # Install a package
      raiku info <package>          # Show package details
      raiku list                    # Show installed packages
      raiku update --all            # Update all packages
      raiku uninstall <package>     # Remove a package
      raiku publish                 # Prepare your package for contribution
      raiku validate                # Validate package structure
      raiku index --rebuild         # Rebuild index from UserSub/
      raiku cache --info            # Show cache statistics
      raiku doctor                  # Check build tool availability
      raiku config list             # View/edit configuration
      raiku trust add <package>     # Trust a package's build command
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


# -----------------------------------------------------------------------
# Original commands
# -----------------------------------------------------------------------
from cli.commands.sync      import sync_cmd
from cli.commands.search    import search_cmd
from cli.commands.install   import install_cmd
from cli.commands.publish   import publish_cmd
from cli.commands.validate  import validate_cmd

# -----------------------------------------------------------------------
# New commands
# -----------------------------------------------------------------------
from cli.commands.list_cmd  import list_cmd
from cli.commands.uninstall import uninstall_cmd
from cli.commands.info      import info_cmd
from cli.commands.update    import update_cmd
from cli.commands.index_cmd import index_cmd
from cli.commands.cache_cmd import cache_cmd
from cli.commands.doctor    import doctor_cmd
from cli.commands.config_cmd import config_cmd
from cli.commands.trust_cmd  import trust_cmd

# -----------------------------------------------------------------------
# Register all
# -----------------------------------------------------------------------
main.add_command(sync_cmd,      name="sync")
main.add_command(search_cmd,    name="search")
main.add_command(install_cmd,   name="install")
main.add_command(publish_cmd,   name="publish")
main.add_command(validate_cmd,  name="validate")
main.add_command(list_cmd,      name="list")
main.add_command(uninstall_cmd, name="uninstall")
main.add_command(info_cmd,      name="info")
main.add_command(update_cmd,    name="update")
main.add_command(index_cmd,     name="index")
main.add_command(cache_cmd,     name="cache")
main.add_command(doctor_cmd,    name="doctor")
main.add_command(config_cmd,    name="config")
main.add_command(trust_cmd,     name="trust")


if __name__ == "__main__":
    main()
