# apiscope/app.py

import typer

from apiscope.add.app import app as add_app
from apiscope.add.constants import COMMAND_NAME as ADD_COMMAND_NAME
from apiscope.constants import MESSAGE_TEMPLATES
from apiscope.context import RootOptions
from apiscope.output import OutputFormat, Report, emit_report
from apiscope.preflight import PreflightError, run_preflight

# ==============================================================================
# app
# ==============================================================================


app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help=MESSAGE_TEMPLATES["root.help.app"],
)

app.add_typer(add_app, name=ADD_COMMAND_NAME)

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
        help=MESSAGE_TEMPLATES["root.help.option.global"],
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help=MESSAGE_TEMPLATES["root.help.option.json"],
    ),
) -> None:
    output_format = OutputFormat.JSON if json_output else OutputFormat.TEXT
    root_options = RootOptions(global_only=global_only, output_format=output_format)
    try:
        runtime_context = run_preflight(options=root_options)
    except PreflightError as error:
        emit_report(
            Report(
                status="error",
                scope="home" if global_only else "project",
                action="preflight",
                code=error.code,
                meta=error.values,
            ),
            output_format=output_format,
            message_templates=MESSAGE_TEMPLATES,
        )
        raise typer.Exit(code=1) from error
    ctx.obj = runtime_context
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
