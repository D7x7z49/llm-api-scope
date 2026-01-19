# apiscope/cli.py
import click

from .core.config import GLOBAL_CONFIG
from .commands.init import init_command
from .commands.list import list_command
from .commands.search import search_command
from .commands.describe import describe_command


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    LLM API Scope - Index, search, and query API documentation.
    """
    # Try to load config automatically
    try:
        GLOBAL_CONFIG.load()
    except RuntimeError:
        # Not initialized yet, that's okay for init command
        pass

    # Store in context for commands that need explicit access
    ctx.obj = GLOBAL_CONFIG


# Register commands using decorator pattern
cli.add_command(init_command, name="init")
cli.add_command(list_command, name="list")
cli.add_command(search_command, name="search")
cli.add_command(describe_command, name="describe")

if __name__ == "__main__":
    cli()
