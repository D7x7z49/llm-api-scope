# apiscope/add/app.py

from pathlib import Path
from re import fullmatch
from typing import cast

import typer
from pydantic import BaseModel, ValidationError

from apiscope.add.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.add.context import AddCommandContext
from apiscope.add.preflight import run_preflight
from apiscope.add.schema import AddOptions
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
from apiscope.output import Report, emit_report
from apiscope.schema import (
    SOURCE_NAME_PATTERN,
    SOURCE_SELECTOR_ALL,
    DocumentType,
    GlobalConfigFile,
    ProjectConfigFile,
    RuntimeSource,
)

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["add.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    name: str = typer.Argument(..., help=MESSAGE_TEMPLATES["add.help.argument.name"]),
    source: str = typer.Argument(..., help=MESSAGE_TEMPLATES["add.help.argument.source"]),
    doc_type: str = typer.Option(..., "--type", help=MESSAGE_TEMPLATES["add.help.option.type"]),
    ttl: int | None = typer.Option(None, "--ttl", help=MESSAGE_TEMPLATES["add.help.option.ttl"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("add.error.runtime_context_unavailable")

    try:
        if name == SOURCE_SELECTOR_ALL:
            raise MessageError("add.error.reserved_name", {"name": name})
        if fullmatch(SOURCE_NAME_PATTERN, name) is None:
            raise MessageError("add.error.invalid_name", {"name": name})
        options = AddOptions(name=name, doc_type=cast(DocumentType, doc_type), doc_src=source, doc_ttl=ttl)
        command_context = AddCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        _add_source(command_context)
    except ValidationError:
        error = MessageError("add.error.invalid_options", {"name": name})
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"name": options.name, "type": options.doc_type},
        ),
        output_format=runtime_context.options.output_format,
    )


def _add_source(command_context: AddCommandContext) -> None:
    runtime = command_context.runtime
    path, model = _config_target(runtime)
    try:
        config_file = ensure_config_file(path, model, schema_ref=CONFIG_SCHEMA_REF)
    except ConfigError as error:
        raise MessageError("add.error.persistence.read_failed", {"path": str(path)}) from error

    sources = extract_config_sources(config_file)
    if command_context.options.name in sources:
        raise MessageError("add.error.duplicate_name", {"name": command_context.options.name})

    source = RuntimeSource(
        doc_type=command_context.options.doc_type,
        doc_src=command_context.options.doc_src,
        doc_ttl=command_context.options.doc_ttl,
    )
    sources[command_context.options.name] = source
    updated_config = with_config_sources(config_file, sources)
    try:
        save_config_file(path, updated_config)
    except ConfigError as error:
        raise MessageError("add.error.persistence.write_failed", {"path": str(path)}) from error


def _config_target(runtime: RuntimeContext) -> tuple[Path, type[BaseModel]]:
    if runtime.options.global_only:
        return runtime.paths.home.config, GlobalConfigFile
    if runtime.paths.project is None:
        raise MessageError("add.error.project_required")
    return runtime.paths.project.config, ProjectConfigFile


def _emit_error(runtime: RuntimeContext, error: MessageError) -> None:
    emit_report(
        Report(
            status="error",
            scope=runtime.scope,
            action=COMMAND_NAME,
            code=error.code,
            meta=error.values,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
    )
