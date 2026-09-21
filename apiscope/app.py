# apiscope/app.py

import typer

from apiscope.add.app import app as add_app
from apiscope.add.constants import COMMAND_NAME as ADD_COMMAND_NAME
from apiscope.constants import MESSAGE_TEMPLATES
from apiscope.context import RootOptions
from apiscope.list.app import app as list_app
from apiscope.list.constants import COMMAND_NAME as LIST_COMMAND_NAME
from apiscope.output import OutputFormat, Report, emit_report
from apiscope.preflight import PreflightError, run_preflight
from apiscope.remove.app import app as remove_app
from apiscope.remove.constants import COMMAND_NAME as REMOVE_COMMAND_NAME
from apiscope.sync.app import app as sync_app
from apiscope.sync.constants import COMMAND_NAME as SYNC_COMMAND_NAME
from apiscope.view.app import app as view_app
from apiscope.view.constants import COMMAND_NAME as VIEW_COMMAND_NAME

# ==============================================================================
# app
# ==============================================================================


app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help=MESSAGE_TEMPLATES["root.help.app"],
)

app.add_typer(add_app, name=ADD_COMMAND_NAME)
app.add_typer(remove_app, name=REMOVE_COMMAND_NAME)
app.add_typer(list_app, name=LIST_COMMAND_NAME)
app.add_typer(sync_app, name=SYNC_COMMAND_NAME)
app.add_typer(view_app, name=VIEW_COMMAND_NAME)

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
