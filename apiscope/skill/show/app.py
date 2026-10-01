# apiscope/skill/show/app.py

from __future__ import annotations

import typer

from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report
from apiscope.skill.constants import MESSAGE_TEMPLATES as SKILL_MESSAGE_TEMPLATES
from apiscope.skill.constants import SKILL_NAME
from apiscope.skill.show.constants import COMMAND_NAME, CONTENT_TEMPLATE, MESSAGE_TEMPLATES
from apiscope.skill.show.context import ShowCommandContext
from apiscope.skill.show.preflight import run_preflight
from apiscope.skill.show.schema import ShowOptions
from apiscope.usage import render_usage

# ==============================================================================
# constants
# ==============================================================================

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **SKILL_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["skill.show.help.command"],
    subcommand_metavar="",
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    runtime_context = _runtime_context(ctx)
    try:
        command_context = ShowCommandContext(runtime=runtime_context, options=ShowOptions())
        run_preflight(command_context)
        content = _content(ctx)
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    lines = content.splitlines()
    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"name": SKILL_NAME},
            data=list(lines),
            extra={"count": len(lines)},
        ),
        output_format=runtime_context.options.output_format,
        body=content,
    )


# ==============================================================================
# helpers
# ==============================================================================


def _content(ctx: typer.Context) -> str:
    usage = render_usage(ctx.find_root().command).rstrip("\n")
    return CONTENT_TEMPLATE.format(usage=usage).rstrip("\n")


def _runtime_context(ctx: typer.Context) -> RuntimeContext:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("skill.error.runtime_context_unavailable")
    return runtime_context


def _emit_error(runtime_context: RuntimeContext, error: MessageError) -> None:
    emit_report(
        Report(
            status="error",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            code=error.code,
            meta=error.values,
        ),
        output_format=runtime_context.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
    )
