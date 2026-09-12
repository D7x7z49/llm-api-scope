# apiscope/app.py

import typer

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
def main_callback(ctx: typer.Context) -> None:
    try:
        command_context = run_preflight()
    except PreflightError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    command_context.command_name = ctx.invoked_subcommand
    ctx.obj = command_context
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
