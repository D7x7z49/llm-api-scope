# apiscope/app.py

import typer

from apiscope.add.app import app as add_app
from apiscope.add.constants import COMMAND_NAME as ADD_COMMAND_NAME
from apiscope.bookmark.app import app as bookmark_app
from apiscope.bookmark.constants import COMMAND_NAME as BOOKMARK_COMMAND_NAME
from apiscope.config import ConfigError, build_home_paths, resolve_home
from apiscope.constants import MESSAGE_TEMPLATES
from apiscope.context import RootOptions
from apiscope.list.app import app as list_app
from apiscope.list.constants import COMMAND_NAME as LIST_COMMAND_NAME
from apiscope.lock import LockError, acquire_write_lock
from apiscope.output import OutputFormat, Report, emit_report
from apiscope.preflight import PreflightError, run_preflight, run_read_preflight
from apiscope.read.app import app as read_app
from apiscope.read.constants import COMMAND_NAME as READ_COMMAND_NAME
from apiscope.remove.app import app as remove_app
from apiscope.remove.constants import COMMAND_NAME as REMOVE_COMMAND_NAME
from apiscope.schema import ConfigScope
from apiscope.skill.app import app as skill_app
from apiscope.skill.constants import COMMAND_NAME as SKILL_COMMAND_NAME
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
app.add_typer(read_app, name=READ_COMMAND_NAME)
app.add_typer(list_app, name=LIST_COMMAND_NAME)
app.add_typer(sync_app, name=SYNC_COMMAND_NAME)
app.add_typer(view_app, name=VIEW_COMMAND_NAME)
app.add_typer(skill_app, name=SKILL_COMMAND_NAME)
app.add_typer(bookmark_app, name=BOOKMARK_COMMAND_NAME)

# write commands prepare assets; read commands only load and project
_WRITE_COMMANDS = {ADD_COMMAND_NAME, REMOVE_COMMAND_NAME, SYNC_COMMAND_NAME}

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
        if ctx.invoked_subcommand in _WRITE_COMMANDS:
            lock = acquire_write_lock(build_home_paths(resolve_home()).root)
            ctx.call_on_close(lock.release)
            runtime_context = run_preflight(options=root_options)
        else:
            runtime_context = run_read_preflight(options=root_options)
    except (PreflightError, ConfigError, LockError) as error:
        emit_report(
            Report(
                status="error",
                scope=ConfigScope.HOME if global_only else ConfigScope.PROJECT,
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
