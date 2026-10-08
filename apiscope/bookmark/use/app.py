# apiscope/bookmark/use/app.py

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from apiscope.bookmark.constants import MESSAGE_TEMPLATES as BOOKMARK_MESSAGE_TEMPLATES
from apiscope.bookmark.context import resolve_context
from apiscope.bookmark.resolve import base_directory, resolve_read_target, resolve_view_target
from apiscope.bookmark.schema import BookmarkEntry, BookmarkFile
from apiscope.bookmark.store import entry_status, load_bookmarks
from apiscope.bookmark.use.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.bookmark.use.context import UseCommandContext
from apiscope.bookmark.use.preflight import run_preflight
from apiscope.bookmark.use.schema import UseOptions
from apiscope.cache import CacheMetadata, digest_content
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report
from apiscope.read_lib.registry import read_content
from apiscope.read_lib.schema import ReadResult

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **BOOKMARK_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["bookmark.use.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@dataclass(frozen=True, slots=True)
class UseResult:
    meta: dict[str, object]
    data: list[Any]
    extra: dict[str, object]
    body: str


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    bookmark_id: str = typer.Argument(..., metavar="ID", help=MESSAGE_TEMPLATES["bookmark.use.help.argument.id"]),
) -> None:
    runtime_context = resolve_context(ctx)
    try:
        options = UseOptions(id=bookmark_id)
        command_context = UseCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        entry = _entry(runtime_context, options.id)
        result = _run(runtime_context, entry)
    except ValidationError as error:
        _emit_error(runtime_context, MessageError("bookmark.use.error.id_not_found", {"id": bookmark_id}))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta=result.meta,
            data=result.data,
            extra=result.extra,
        ),
        output_format=runtime_context.options.output_format,
        body=result.body,
    )


# ==============================================================================
# dispatch
# ==============================================================================


def _entry(runtime: RuntimeContext, bookmark_id: str) -> BookmarkEntry:
    data = load_bookmarks(runtime)
    entry = data.bookmarks.get(bookmark_id)
    if entry is None:
        raise MessageError("bookmark.use.error.id_not_found", {"id": bookmark_id})
    if entry.removed:
        raise MessageError("bookmark.use.error.removed", {"id": bookmark_id})
    return entry


def _run(runtime: RuntimeContext, entry: BookmarkEntry) -> UseResult:
    if entry.mode == "file":
        return _run_file(runtime, entry)
    if entry.mode == "view":
        return _run_view(runtime, entry)
    if entry.mode == "group":
        return _run_group(runtime, entry)
    return _run_read(runtime, entry)


# ==============================================================================
# file mode
# ==============================================================================


def _run_file(runtime: RuntimeContext, entry: BookmarkEntry) -> UseResult:
    path = Path(entry.target).expanduser()
    if not path.is_absolute():
        path = base_directory(runtime) / path
    if not path.is_file() or digest_content(path) != entry.expected_digest:
        raise MessageError("bookmark.use.error.invalid", {"id": entry.id})

    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        result = ReadResult(target=str(path), kind="binary", size=len(raw))
    else:
        result = ReadResult(target=str(path), kind="text", content=_slice(text, entry), encoding="utf-8")
    return UseResult(
        meta=_meta(entry),
        data=result.as_data(),
        extra=result.as_extra("local"),
        body=result.render_body(),
    )


# a file bookmark reads the whole file unless it names a line range
def _slice(text: str, entry: BookmarkEntry) -> str:
    if entry.start is None and entry.offset is None:
        return text
    lines = text.splitlines(keepends=True)
    start = entry.start or 0
    end = None if entry.offset is None else start + entry.offset
    return "".join(lines[start:end])


# ==============================================================================
# group mode
# ==============================================================================


def _run_group(runtime: RuntimeContext, entry: BookmarkEntry) -> UseResult:
    data = load_bookmarks(runtime)
    members = [data.bookmarks[member] for member in entry.members if member in data.bookmarks]
    rows = [_member_row(runtime, data, member) for member in members]
    body = (
        "\n".join(f"- [{row['id']}] {row['mode']} {row['target']} ({row['status']})" for row in rows)
        or MESSAGE_TEMPLATES["bookmark.use.body.empty"]
    )
    return UseResult(
        meta=_meta(entry),
        data=rows,
        extra={"entries": len(members)},
        body=body,
    )


def _member_row(runtime: RuntimeContext, data: BookmarkFile, entry: BookmarkEntry) -> dict[str, str]:
    return {
        "id": entry.id,
        "mode": entry.mode,
        "target": entry.target,
        "status": entry_status(runtime, data.bookmarks, entry),
    }


# ==============================================================================
# cache modes
# ==============================================================================


def _run_view(runtime: RuntimeContext, entry: BookmarkEntry) -> UseResult:
    resolved = resolve_view_target(runtime, entry.target)
    _require_expected(entry, resolved.metadata)
    nodes = resolved.nodes
    body = "\n".join(f"- [{node.index}] {node.key}" for node in nodes) or MESSAGE_TEMPLATES["bookmark.use.body.empty"]
    return UseResult(
        meta=_meta(entry),
        data=[node.as_data() for node in nodes],
        extra={"entries": len(nodes), "cache": resolved.snapshot.inspection.state},
        body=body,
    )


def _run_read(runtime: RuntimeContext, entry: BookmarkEntry) -> UseResult:
    resolved = resolve_read_target(runtime, entry.target)
    _require_expected(entry, resolved.metadata)
    content = read_content(resolved.source.doc_type, resolved.snapshot.content, resolved.metadata, resolved.node)
    return UseResult(
        meta=_meta(entry),
        data=content.as_data(),
        extra=content.as_extra(resolved.snapshot.inspection.state),
        body=content.render_body(),
    )


# the stored digest is the contract; both cache modes compare it the same way
def _require_expected(entry: BookmarkEntry, metadata: CacheMetadata) -> None:
    if metadata.content_digest != entry.expected_digest:
        raise MessageError("bookmark.use.error.invalid", {"id": entry.id})


# ==============================================================================
# helpers
# ==============================================================================


def _meta(entry: BookmarkEntry) -> dict[str, object]:
    return {"id": entry.id, "mode": entry.mode, "target": entry.target}


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
