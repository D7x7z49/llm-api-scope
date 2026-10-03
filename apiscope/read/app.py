# apiscope/read/app.py
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
from apiscope.read.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.read.context import ReadCommandContext
from apiscope.read.preflight import run_preflight
from apiscope.read.schema import ReadOptions
from apiscope.read_lib.constants import MESSAGE_TEMPLATES as READ_LIB_MESSAGE_TEMPLATES
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.registry import read_content, supports_reading
from apiscope.read_lib.schema import ReadResult
from apiscope.schema import RuntimeSource
from apiscope.source import SourceResolutionError, parse_source
from apiscope.view_lib.address import split_address
from apiscope.view_lib.constants import MESSAGE_TEMPLATES as VIEW_LIB_MESSAGE_TEMPLATES
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import MessageHintError, ProjectionError
from apiscope.view_lib.hint import render_route_hint
from apiscope.view_lib.registry import build_tree
from apiscope.view_lib.schema import IndexedNode
from apiscope.view_lib.tree import SourceTree, hint_nodes

_MESSAGE_TEMPLATES = {
    **ROOT_MESSAGE_TEMPLATES,
    **VIEW_LIB_MESSAGE_TEMPLATES,
    **READ_LIB_MESSAGE_TEMPLATES,
    **MESSAGE_TEMPLATES,
}

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["read.help.command"],
    subcommand_metavar="",
)


@dataclass(frozen=True, slots=True)
class ReadCommandResult:
    cache_state: str
    content: ReadResult
    target: str


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    address: str = typer.Argument(..., help=MESSAGE_TEMPLATES["read.help.argument.address"]),
    index: str | None = typer.Argument(None, help=MESSAGE_TEMPLATES["read.help.argument.index"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("read.error.runtime_context_unavailable")

    try:
        options = ReadOptions(address=address, index=index)
        command_context = ReadCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        name, route = split_address(options.address, runtime_context.config.source)
        source = runtime_context.config.source.get(name)
        if source is None:
            raise MessageError("read.error.name_not_found", {"name": name})
        result = _run_read(command_context, source, name=name, route=route)
    except ValidationError as error:
        message = MessageError("read.error.invalid_options")
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    content = result.content
    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"name": name, "target": result.target},
            data=content.as_data(),
            extra=content.as_extra(result.cache_state),
        ),
        output_format=runtime_context.options.output_format,
        body=content.render_body(),
    )


def _run_read(
    command_context: ReadCommandContext,
    source: RuntimeSource,
    *,
    name: str,
    route: str,
) -> ReadCommandResult:
    runtime = command_context.runtime
    options = command_context.options
    base_dir = runtime.paths.project.root if runtime.paths.project is not None else Path.cwd()
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except SourceResolutionError as error:
        raise MessageError("read.error.source_invalid", {"name": name}) from error

    if not supports_reading(source.doc_type):
        raise MessageError(ReadReason.READER_UNSUPPORTED, {"name": name, "doc_type": source.doc_type})

    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    snapshot = load_content(runtime.paths.home.cache, parsed, ttl_days=ttl_days)
    inspection = snapshot.inspection
    _require_cache(name, inspection)
    metadata = inspection.metadata
    if metadata is None:
        raise MessageError("read.error.cache_invalid", {"name": name})

    try:
        tree = build_tree(source.doc_type, snapshot.content, metadata)
        scoped_nodes = tree.select(route)
        node = _select_node(tree, scoped_nodes, options, route=route)
        if node.path is None:
            raise MessageError("read.error.target_invalid", {"target": options.address})
        content = read_content(
            source.doc_type,
            snapshot.content,
            metadata,
            node,
        )
    except ProjectionError as error:
        raise _projection_message(error, name=name, address=options.address) from error
    except ReadError as error:
        values = {"name": name, **error.values}
        values.setdefault("target", options.index or options.address)
        raise MessageError(error.code, values) from error
    except OSError as error:
        raise MessageError("read.error.content_invalid", {"name": name}) from error

    return ReadCommandResult(cache_state=inspection.state, content=content, target=node.path)


def _select_node(
    tree: SourceTree,
    scoped_nodes: tuple[IndexedNode, ...],
    options: ReadOptions,
    *,
    route: str,
) -> IndexedNode:
    if options.index is None:
        node: IndexedNode | None
        if route not in {"", "."}:
            node = tree.resolve(route)
            children = tree.children_of(node, scoped_nodes)
        else:
            indexed = tree.indexed()
            node = indexed[0] if len(indexed) == 1 else None
            children = scoped_nodes if node is None else ()
        if node is None or not node.is_leaf:
            target = (node.path or node.key) if node is not None else options.address
            raise MessageHintError(
                "read.error.target_not_leaf",
                {"target": target},
                hint_address=options.address,
                hint_nodes=hint_nodes(children),
            )
        return node

    node = next((candidate for candidate in scoped_nodes if candidate.index == options.index), None)
    if node is None:
        raise MessageError("view_lib.projection.index_not_found", {"index": options.index})
    if not node.is_leaf:
        children = tree.children_of(node, scoped_nodes)
        raise MessageHintError(
            "read.error.target_not_leaf",
            {"target": node.path or node.key},
            hint_address=options.address,
            hint_nodes=hint_nodes(children),
        )
    return node


def _require_cache(name: str, inspection: CacheInspection) -> None:
    if inspection.state == "missing":
        raise MessageError("read.error.cache_missing", {"name": name})
    if inspection.state == "invalid" or inspection.metadata is None:
        raise MessageError("read.error.cache_invalid", {"name": name})


def _projection_message(error: ProjectionError, *, name: str, address: str) -> MessageError:
    values = dict(error.values)
    values["name"] = name
    values["address"] = address
    if "path" in values:
        values.setdefault("target", values["path"])
    if error.reason_code == ProjectionReason.PATH_INVALID.value:
        return MessageError("read.error.target_invalid", values)
    if error.reason_code == ProjectionReason.PATH_NOT_FOUND.value:
        prefix = str(error.values.get("prefix") or ".")
        nodes = error.values.get("nodes") or []
        hint_address = name if prefix in {"", "."} else f"{name}/{prefix}"
        return MessageHintError(error.reason_code, values, hint_address=hint_address, hint_nodes=nodes)
    return MessageError(error.reason_code, values)


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
