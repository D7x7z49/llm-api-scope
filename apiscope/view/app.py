# apiscope/view/app.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from pydantic import ValidationError

from apiscope.cache import CacheInspection
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.content import load_content
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report
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
    context_settings={"allow_interspersed_args": True},
)


# ==============================================================================
# types
# ==============================================================================


@dataclass(frozen=True, slots=True)
class ViewResult:
    cache_state: str
    anchor: IndexedNode | None
    nodes: tuple[IndexedNode, ...]


# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    address: str = typer.Argument(..., help=MESSAGE_TEMPLATES["view.help.argument.address"]),
    depth: int | None = typer.Option(None, "--depth", min=0, help=MESSAGE_TEMPLATES["view.help.option.depth"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("view.error.runtime_context_unavailable")

    try:
        options = ViewOptions(address=address, depth=depth)
        command_context = ViewCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        name, path = split_address(options.address, runtime_context.config.source)
        source = runtime_context.config.source.get(name)
        if source is None:
            raise MessageError("view.error.name_not_found", {"name": name})
        result = _run_view(command_context, source, name=name, path=path)
    except ValidationError as error:
        message = MessageError("view.error.invalid_options")
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    meta: dict[str, object] = {"name": name, "path": path}
    if result.anchor is not None and result.anchor.description:
        meta["description"] = result.anchor.description
    if options.depth is not None:
        meta["depth"] = options.depth
    extra = {"entries": len(result.nodes), "cache": result.cache_state}
    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta=meta,
            data=[node.as_data() for node in result.nodes],
            extra=extra,
        ),
        output_format=runtime_context.options.output_format,
        body=_render_body(result.nodes),
    )


# ==============================================================================
# cache projection
# ==============================================================================


def _run_view(
    command_context: ViewCommandContext,
    source: RuntimeSource,
    *,
    name: str,
    path: str,
) -> ViewResult:
    runtime = command_context.runtime
    options = command_context.options
    base_dir = runtime.paths.project.root if runtime.paths.project is not None else Path.cwd()
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except SourceResolutionError as error:
        raise MessageError("view.error.source_invalid", {"name": name}) from error

    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    snapshot = load_content(runtime.paths.home.cache, parsed, base_dir=base_dir, ttl_days=ttl_days)
    inspection = snapshot.inspection
    _require_cache(name, inspection)
    metadata = inspection.metadata
    if metadata is None:
        raise MessageError("view.error.cache_invalid", {"name": name})

    try:
        tree = build_tree(source.doc_type, snapshot.content, metadata)
        anchor = None
        if tree.normalize_path(path):
            anchor = tree.resolve(path)
        nodes = tree.select(path, depth=options.depth)
    except ProjectionError as error:
        raise _projection_message(error, name=name) from error
    except OSError as error:
        raise MessageError("view.error.projection_failed", {"name": name}) from error

    return ViewResult(
        cache_state=inspection.state,
        anchor=anchor,
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
            scope=runtime.scope,
            action=COMMAND_NAME,
            code=error.code,
            extra=extra,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
        message_values=error.values,
        body=body,
    )
