# apiscope/skill/install/app.py

from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError

from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report
from apiscope.skill.constants import MESSAGE_TEMPLATES as SKILL_MESSAGE_TEMPLATES
from apiscope.skill.constants import SKILL_NAME
from apiscope.skill.install.constants import (
    COMMAND_NAME,
    DEFAULT_INSTALL_TARGET,
    MARKDOWN_TEMPLATE,
    MESSAGE_TEMPLATES,
    SKILL_DESCRIPTION,
    SKILL_FILENAME,
)
from apiscope.skill.install.context import InstallCommandContext
from apiscope.skill.install.preflight import run_preflight
from apiscope.skill.install.schema import InstallOptions
from apiscope.skill.show.constants import CONTENT_TEMPLATE
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
    help=MESSAGE_TEMPLATES["skill.install.help.command"],
    subcommand_metavar="",
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    target: str | None = typer.Argument(None, help=MESSAGE_TEMPLATES["skill.install.help.argument.target"]),
) -> None:
    runtime_context = _runtime_context(ctx)
    try:
        options = InstallOptions(target=target)
        command_context = InstallCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        content = _content(ctx)
        resolved = _resolve_target(options.target)
        _write_skill(resolved, content)
    except ValidationError as error:
        _emit_error(runtime_context, MessageError("skill.install.error.invalid_options"))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error
    except OSError as error:
        message = MessageError("skill.install.error.install_failed", {"path": target or DEFAULT_INSTALL_TARGET})
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"name": SKILL_NAME, "path": str(resolved)},
        ),
        output_format=runtime_context.options.output_format,
    )


# ==============================================================================
# helpers
# ==============================================================================


def _content(ctx: typer.Context) -> str:
    usage = render_usage(ctx.find_root().command).rstrip("\n")
    return CONTENT_TEMPLATE.format(usage=usage).rstrip("\n")


# build the SKILL.md with its yaml meta head, then write the skill directory
def _write_skill(target: Path, content: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    markdown = MARKDOWN_TEMPLATE.format(name=SKILL_NAME, description=SKILL_DESCRIPTION, content=content)
    (target / SKILL_FILENAME).write_text(markdown, encoding="utf-8")


def _runtime_context(ctx: typer.Context) -> RuntimeContext:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("skill.error.runtime_context_unavailable")
    return runtime_context


def _resolve_target(target: str | None) -> Path:
    return Path(target or DEFAULT_INSTALL_TARGET).expanduser()


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
