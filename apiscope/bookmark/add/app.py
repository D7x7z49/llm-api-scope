# apiscope/bookmark/add/app.py

from typing import cast

import typer
from pydantic import ValidationError

from apiscope.bookmark.add.constants import (
    COMMAND_NAME,
    FILE_MISSING_REASON,
    MESSAGE_TEMPLATES,
    TARGET_REASON_TEXTS,
)
from apiscope.bookmark.add.context import AddCommandContext
from apiscope.bookmark.add.preflight import run_preflight
from apiscope.bookmark.add.schema import AddOptions
from apiscope.bookmark.constants import MESSAGE_TEMPLATES as BOOKMARK_MESSAGE_TEMPLATES
from apiscope.bookmark.context import resolve_context
from apiscope.bookmark.resolve import TargetResolutionError, resolve_read_target, resolve_view_target, target_digest
from apiscope.bookmark.schema import BookmarkEntry, BookmarkFile, BookmarkMode
from apiscope.bookmark.store import ensure_bookmarks, load_bookmarks, save_bookmarks, validate_acyclic
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.lock import acquire_write_lock
from apiscope.output import Report, emit_report
from apiscope.validation import describe

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **BOOKMARK_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# the schema field names map to the option labels the user sees
_OPTION_LABELS = {
    "description": "--description",
    "start": "--start",
    "offset": "--offset",
}

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["bookmark.add.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    bookmark_id: str = typer.Argument(..., metavar="ID", help=MESSAGE_TEMPLATES["bookmark.add.help.argument.id"]),
    mode: str = typer.Argument(..., help=MESSAGE_TEMPLATES["bookmark.add.help.argument.mode"]),
    target: list[str] | None = typer.Argument(
        None,
        help=MESSAGE_TEMPLATES["bookmark.add.help.argument.target"],
    ),
    description: str = typer.Option(
        ...,
        "--description",
        help=MESSAGE_TEMPLATES["bookmark.add.help.option.description"],
    ),
    start: int | None = typer.Option(
        None,
        "--start",
        min=0,
        help=MESSAGE_TEMPLATES["bookmark.add.help.option.start"],
    ),
    offset: int | None = typer.Option(
        None,
        "--offset",
        min=1,
        help=MESSAGE_TEMPLATES["bookmark.add.help.option.offset"],
    ),
    force: bool = typer.Option(False, "--force", help=MESSAGE_TEMPLATES["bookmark.add.help.option.force"]),
) -> None:
    runtime_context = resolve_context(ctx)
    try:
        lock = acquire_write_lock(runtime_context.paths.home.root)
        ctx.call_on_close(lock.release)
        options = AddOptions(
            id=bookmark_id,
            mode=cast(BookmarkMode, mode),
            targets=tuple(target or ()),
            description=description,
            start=start,
            offset=offset,
            force=force,
        )
        command_context = AddCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        _add(command_context)
    except ValidationError as error:
        detail = describe(error, _OPTION_LABELS)
        _emit_error(runtime_context, MessageError("bookmark.add.error.invalid_options", {"detail": detail}))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"id": options.id, "mode": options.mode},
        ),
        output_format=runtime_context.options.output_format,
    )


# ==============================================================================
# helpers
# ==============================================================================


def _add(command_context: AddCommandContext) -> None:
    runtime = command_context.runtime
    options = command_context.options
    merged = load_bookmarks(runtime)
    if options.id in merged.bookmarks and not options.force:
        raise MessageError("bookmark.add.error.duplicate_id", {"id": options.id})

    entry = _build_entry(runtime, merged, options)
    validate_acyclic({**merged.bookmarks, options.id: entry})
    data = ensure_bookmarks(runtime)
    data.bookmarks = {**data.bookmarks, options.id: entry}
    save_bookmarks(runtime, data)


def _build_entry(runtime: RuntimeContext, merged: BookmarkFile, options: AddOptions) -> BookmarkEntry:
    if options.mode == "group":
        return _build_group(merged, options)

    if len(options.targets) != 1:
        raise MessageError("bookmark.add.error.target_count", {"mode": options.mode, "count": len(options.targets)})
    if options.mode != "file" and (options.start is not None or options.offset is not None):
        raise MessageError("bookmark.add.error.range_not_allowed")

    target = options.targets[0]
    digest = _target_digest(runtime, options.mode, target)
    return BookmarkEntry(
        id=options.id,
        description=options.description,
        mode=options.mode,
        target=target,
        start=options.start,
        offset=options.offset,
        expected_digest=digest,
    )


# a file target is a path; a cache target uses the shared resolver, so add
# rejects exactly what use cannot project and names the target in the reason
def _target_digest(runtime: RuntimeContext, mode: BookmarkMode, target: str) -> str:
    if mode == "file":
        digest = target_digest(runtime, mode, target)
        if digest is None:
            raise MessageError(
                "bookmark.add.error.target_unresolved",
                {"mode": mode, "target": target, "detail": FILE_MISSING_REASON},
            )
        return digest
    try:
        if mode == "read":
            return resolve_read_target(runtime, target).metadata.content_digest
        return resolve_view_target(runtime, target).metadata.content_digest
    except TargetResolutionError as error:
        raise MessageError(
            "bookmark.add.error.target_unresolved",
            {"mode": mode, "target": target, "detail": TARGET_REASON_TEXTS[error.reason.value]},
        ) from error


def _build_group(merged: BookmarkFile, options: AddOptions) -> BookmarkEntry:
    members = options.targets
    if options.start is not None or options.offset is not None:
        raise MessageError("bookmark.add.error.range_not_allowed")
    if not 5 <= len(members) <= 9:
        raise MessageError("bookmark.add.error.group_needs_members", {"count": len(members)})
    if len(set(members)) != len(members):
        raise MessageError("bookmark.add.error.duplicate_member")
    if options.id in members:
        raise MessageError("bookmark.add.error.self_member", {"id": options.id})
    for member in members:
        if member not in merged.bookmarks:
            raise MessageError("bookmark.add.error.member_not_found", {"id": member})
    return BookmarkEntry(
        id=options.id,
        description=options.description,
        mode="group",
        members=members,
    )


def _emit_error(runtime: RuntimeContext, error: MessageError) -> None:
    emit_report(
        Report(
            status="error",
            scope=runtime.scope,
            action=COMMAND_NAME,
            code=error.code,
            meta=error.meta,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
        message_values=error.message_values,
    )
