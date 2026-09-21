# apiscope/view/app.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import typer
from pydantic import ValidationError

from apiscope.cache import CacheInspection, cache_path, inspect_cache
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, ReportScope, emit_report
from apiscope.schema import RuntimeSource
from apiscope.view._lib.errors import ViewProjectionError, ViewSourceError
from apiscope.view._lib.registry import build_view, parse_source
from apiscope.view._lib.tree import IndexedNode
from apiscope.view.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.view.schema import ViewOptions

# ==============================================================================
# constants
# ==============================================================================


_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

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
        options = ViewOptions(name=name, path=path)
        source = runtime_context.config.source.get(options.name)
        if source is None:
            raise MessageError("view.error.name_not_found", {"name": options.name})
        result = _run_view(runtime_context, options, source)
    except ValidationError as error:
        message = MessageError("view.error.invalid_options")
        _emit_error(runtime_context, message)
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


def _run_view(runtime: RuntimeContext, options: ViewOptions, source: RuntimeSource) -> ViewResult:
    base_dir = runtime.paths.project.root if runtime.paths.project is not None else Path.cwd()
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except ViewSourceError as error:
        raise MessageError("view.error.source_invalid", {"name": options.name}) from error

    entry = cache_path(runtime.paths.home.cache, parsed.canonical)
    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    inspection = inspect_cache(
        entry,
        ttl_days=ttl_days,
        expected_source=parsed.canonical,
        expected_doc_type=parsed.doc_type,
    )
    _require_cache(options.name, inspection)
    metadata = inspection.metadata
    if metadata is None:
        raise MessageError("view.error.cache_invalid", {"name": options.name})

    try:
        tree = build_view(source.doc_type, entry / "content", metadata)
        nodes = tree.select(options.path)
    except ViewProjectionError as error:
        raise _projection_message(options, error) from error
    except (OSError, TypeError, ValueError) as error:
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
# error translation
# ==============================================================================


def _projection_message(options: ViewOptions, error: ViewProjectionError) -> MessageError:
    values = dict(error.values)
    values.setdefault("name", options.name)
    code = error.reason_code
    if code == "view.path_invalid":
        return MessageError("view.error.path_invalid", values)
    if code == "view.path_not_found":
        return MessageError("view.error.path_not_found", values)
    if code == "view.path_ambiguous":
        return MessageError("view.error.path_ambiguous", values)
    if code == "view.content_invalid":
        return MessageError("view.error.content_invalid", values)
    if code == "view.document_invalid":
        return MessageError("view.error.document_invalid", values)
    return MessageError("view.error.projection_failed", values)


# ==============================================================================
# report rendering
# ==============================================================================


def _render_body(nodes: tuple[IndexedNode, ...]) -> str:
    if not nodes:
        return "(no entries)"
    lines: list[str] = []
    for node in nodes:
        if node.kind == "key_value":
            lines.append(f"- [{node.index}] {node.key}: {node.value}")
        else:
            lines.append(f"- [{node.index}] {node.value}")
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
