# apiscope/cli.py
"""
Main CLI entry point for apiscope.
Pre-loads configuration state and provides it to all subcommands.
"""
import click
from .core.config import load_or_init_config, ConfigState
from .commands.init import init_command
from .commands.list import list_command

def create_cli() -> click.Group:
    """
    Create CLI application with pre-loaded configuration.

    Returns:
        Configured Click CLI group.
    """

    @click.group()
    @click.pass_context
    def cli(ctx: click.Context) -> None:
        """
        LLM API Scope - Index, search, and query API documentation.

        This tool helps LLMs and developers work with structured API
        documentation (OpenAPI specifications) through a unified interface.
        """
        # Pre-load configuration state for all commands
        ctx.obj = load_or_init_config()
        ctx.ensure_object(ConfigState)

    # Register subcommands
    cli.add_command(init_command, name="init")
    cli.add_command(list_command, name="list")

    return cli

# Create the main CLI instance
cli = create_cli()

if __name__ == "__main__":
    cli()
