# apiscope/main.py
#
# structure convention:
#
#   subcommands live under apiscope/<group>/ as subdirectory packages.
#   each subdirectory contains:
#
#     app.py    — command definitions (typer.Typer app)
#     schema.py — context object for this command group (read-only contract)
#
#   parent callbacks inject ctx.obj with CommandContext(config=...).
#   subcommand callbacks extend ctx.obj.extras with group-specific keys.
#   schema.py exists solely to document the context shape — no runtime logic.

import typer

from apiscope.config import APP_NAME, DEFAULT_ROOT, get_config
from apiscope.openapi import openapi_app
from apiscope.schema import CommandContext

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help="a reader for network resources",
)

# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
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


@app.command(help="check that apiscope is installed and working")
def health(ctx: typer.Context) -> None:
    cache_dir = DEFAULT_ROOT / "cache"
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"{APP_NAME} is healthy")


# ==============================================================================
# entry point
# ==============================================================================

if __name__ == "__main__":
    app()
