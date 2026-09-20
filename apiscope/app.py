# apiscope/app.py

import typer

from apiscope.context import RootOptions
from apiscope.preflight import PreflightError, run_preflight

# ==============================================================================
# app
# ==============================================================================


app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help="read and cache structured documents from remote for LLM agents",
)

# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    global_only: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="use home configuration and skip project discovery",
    ),
) -> None:
    root_options = RootOptions(global_only=global_only)
    try:
        runtime_context = run_preflight(options=root_options)
    except PreflightError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    ctx.obj = runtime_context
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
