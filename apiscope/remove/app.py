# apiscope/remove/app.py

from pathlib import Path

import typer
from pydantic import BaseModel, ValidationError

from apiscope.config import (
    ConfigError,
    ensure_config_file,
    extract_config_sources,
    save_config_file,
    with_config_sources,
)
from apiscope.constants import CONFIG_SCHEMA_REF
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, ReportScope, emit_report
from apiscope.remove.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.remove.context import RemoveCommandContext
from apiscope.remove.preflight import run_preflight
from apiscope.remove.schema import RemoveOptions
from apiscope.schema import SOURCE_SELECTOR_ALL, GlobalConfigFile, ProjectConfigFile

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["remove.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    name: str = typer.Argument(..., help=MESSAGE_TEMPLATES["remove.help.argument.name"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("remove.error.runtime_context_unavailable")

    try:
        if name == SOURCE_SELECTOR_ALL:
            raise MessageError("remove.error.reserved_name", {"name": name})
        options = RemoveOptions(name=name)
        command_context = RemoveCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        _remove_source(command_context)
    except ValidationError:
        error = MessageError("remove.error.invalid_options", {"name": name})
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=_scope(runtime_context),
            action=COMMAND_NAME,
            meta={"name": options.name},
        ),
        output_format=runtime_context.options.output_format,
    )


def _remove_source(command_context: RemoveCommandContext) -> None:
    runtime = command_context.runtime
    path, model = _config_target(runtime)
    try:
        config_file = ensure_config_file(path, model, schema_ref=CONFIG_SCHEMA_REF)
    except ConfigError as error:
        raise MessageError("remove.error.persistence.read_failed", {"path": str(path)}) from error

    sources = extract_config_sources(config_file)
    if command_context.options.name not in sources:
        raise MessageError("remove.error.name_not_found", {"name": command_context.options.name})

    del sources[command_context.options.name]
    updated_config = with_config_sources(config_file, sources)
    try:
        save_config_file(path, updated_config)
    except ConfigError as error:
        raise MessageError("remove.error.persistence.write_failed", {"path": str(path)}) from error


def _config_target(runtime: RuntimeContext) -> tuple[Path, type[BaseModel]]:
    if runtime.options.global_only:
        return runtime.paths.home.config, GlobalConfigFile
    if runtime.paths.project is None:
        raise MessageError("remove.error.project_required")
    return runtime.paths.project.config, ProjectConfigFile


def _scope(runtime: RuntimeContext) -> ReportScope:
    return "home" if runtime.options.global_only else "project"


def _emit_error(runtime: RuntimeContext, error: MessageError) -> None:
    emit_report(
        Report(
            status="error",
            scope=_scope(runtime),
            action=COMMAND_NAME,
            code=error.code,
            meta=error.values,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
    )
