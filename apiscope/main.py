# apiscope/main.py
#
# Structure convention:
#
#   Subcommands live under apiscope/<group>/ as subdirectory packages.
#   Each subdirectory contains:
#
#     app.py    — command definitions (typer.Typer app)
#     schema.py — context object for this command group (read-only contract)
#
#   Parent callbacks inject ctx.obj with CommandContext(config=...).
#   Subcommand callbacks extend ctx.obj.extras with group-specific keys.
#   schema.py exists solely to document the context shape — no runtime logic.

import typer

from apiscope.config import APP_NAME, DEFAULT_ROOT, get_config
from apiscope.openapi import openapi_app
from apiscope.schema import CommandContext

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(rich_markup_mode=None, pretty_exceptions_enable=False)

# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    """A reader for network resources."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        return
    ctx.obj = CommandContext(config=get_config())


# ==============================================================================
# subcommands
# ==============================================================================

app.add_typer(openapi_app, name="openapi")

# ==============================================================================
# commands
# ==============================================================================


@app.command()
def health(ctx: typer.Context) -> None:
    """Check that apiscope is installed and working."""
    cache_dir = DEFAULT_ROOT / "cache"
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"{APP_NAME} is healthy")


# ==============================================================================
# entry point
# ==============================================================================

if __name__ == "__main__":
    app()
