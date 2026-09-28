# apiscope/view/app.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import typer
from pydantic import ValidationError

from apiscope.cache import CacheInspection
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.content import load_content
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, ReportScope, emit_report
from apiscope.schema import RuntimeSource
from apiscope.source import SourceResolutionError, parse_source
from apiscope.view.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.view.context import ViewCommandContext
from apiscope.view.preflight import run_preflight
from apiscope.view.schema import ViewOptions
from apiscope.view_lib.address import split_address
from apiscope.view_lib.constants import MESSAGE_TEMPLATES as VIEW_LIB_MESSAGE_TEMPLATES
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import MessageHintError, ProjectionError
from apiscope.view_lib.hint import render_route_hint
from apiscope.view_lib.registry import build_tree
from apiscope.view_lib.schema import IndexedNode

# ==============================================================================
# constants
# ==============================================================================


_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **VIEW_LIB_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# ==============================================================================
# app
# ==============================================================================


app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["view.help.command"],
    subcommand_metavar="",
)


# ==============================================================================
# types
# ==============================================================================


@dataclass(frozen=True, slots=True)
class ViewResult:
    cache_state: str
    nodes: tuple[IndexedNode, ...]


# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    name: str = typer.Argument(..., help=MESSAGE_TEMPLATES["view.help.argument.name"]),
    path: str | None = typer.Argument(None, help=MESSAGE_TEMPLATES["view.help.argument.path"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("view.error.runtime_context_unavailable")

    try:
        if path is None:
            name, path = split_address(name, runtime_context.config.source)
        options = ViewOptions(name=name, path=path)
        command_context = ViewCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        source = runtime_context.config.source.get(options.name)
        if source is None:
            raise MessageError("view.error.name_not_found", {"name": options.name})
        result = _run_view(command_context, source)
    except ValidationError as error:
        message = MessageError("view.error.invalid_options")
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error
    except ProjectionError as error:
        _emit_error(runtime_context, _projection_message(error, name=options.name))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=_scope(runtime_context),
            action=COMMAND_NAME,
            meta={"name": options.name, "path": options.path or "."},
            data=[node.as_data() for node in result.nodes],
            extra={
                "entries": len(result.nodes),
                "cache": result.cache_state,
                "index": "temporary",
            },
        ),
        output_format=runtime_context.options.output_format,
        body=_render_body(result.nodes),
        foot=_render_foot(result),
    )


# ==============================================================================
# cache projection
# ==============================================================================


def _run_view(command_context: ViewCommandContext, source: RuntimeSource) -> ViewResult:
    runtime = command_context.runtime
    options = command_context.options
    base_dir = runtime.paths.project.root if runtime.paths.project is not None else Path.cwd()
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except SourceResolutionError as error:
        raise MessageError("view.error.source_invalid", {"name": options.name}) from error

    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    snapshot = load_content(runtime.paths.home.cache, parsed, ttl_days=ttl_days)
    inspection = snapshot.inspection
    _require_cache(options.name, inspection)
    metadata = inspection.metadata
    if metadata is None:
        raise MessageError("view.error.cache_invalid", {"name": options.name})

    try:
        tree = build_tree(source.doc_type, snapshot.content, metadata)
        nodes = tree.select(options.path)
    except OSError as error:
        raise MessageError("view.error.projection_failed", {"name": options.name}) from error

    return ViewResult(
        cache_state=inspection.state,
        nodes=nodes,
    )


# ==============================================================================
# cache validation
# ==============================================================================


def _require_cache(name: str, inspection: CacheInspection) -> None:
    if inspection.state == "missing":
        raise MessageError("view.error.cache_missing", {"name": name})
    if inspection.state == "invalid" or inspection.metadata is None:
        raise MessageError("view.error.cache_invalid", {"name": name})


# ==============================================================================
# report rendering
# ==============================================================================


def _render_body(nodes: tuple[IndexedNode, ...]) -> str:
    if not nodes:
        return MESSAGE_TEMPLATES["view.body.empty"]
    lines: list[str] = []
    for node in nodes:
        description = f": {node.description}" if node.description else ""
        lines.append(f"- [{node.index}] {node.key}{description}")
    return "\n".join(lines)


def _render_foot(result: ViewResult) -> str:
    return json.dumps(
        {
            "entries": len(result.nodes),
            "cache": result.cache_state,
            "index": "temporary",
        },
        ensure_ascii=False,
        indent=2,
    )


def _scope(runtime: RuntimeContext) -> ReportScope:
    if runtime.options.global_only or runtime.paths.project is None:
        return "home"
    return "project"


def _projection_message(error: ProjectionError, *, name: str) -> MessageError:
    if error.reason_code == ProjectionReason.PATH_NOT_FOUND:
        prefix = str(error.values.get("prefix") or ".")
        nodes = error.values.get("nodes") or []
        address = name if prefix in {"", "."} else f"{name}/{prefix}"
        return MessageHintError(error.reason_code, error.values, hint_address=address, hint_nodes=nodes)
    return MessageError(error.reason_code, error.values)


def _emit_error(runtime: RuntimeContext, error: MessageError) -> None:
    extra: dict[str, object] | None = None
    body: str | None = None
    if isinstance(error, MessageHintError):
        extra = {"address": error.hint_address, "nodes": list(error.hint_nodes)}
        body = render_route_hint(error.hint_address, error.hint_nodes)
    emit_report(
        Report(
            status="error",
            scope=_scope(runtime),
            action=COMMAND_NAME,
            code=error.code,
            extra=extra,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
        message_values=error.values,
        body=body,
    )
