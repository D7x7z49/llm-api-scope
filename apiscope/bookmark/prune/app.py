# apiscope/bookmark/prune/app.py

from collections.abc import Mapping

import typer
from pydantic import ValidationError

from apiscope.bookmark.constants import MESSAGE_TEMPLATES as BOOKMARK_MESSAGE_TEMPLATES
from apiscope.bookmark.context import resolve_context
from apiscope.bookmark.prune.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.bookmark.prune.context import PruneCommandContext
from apiscope.bookmark.prune.preflight import run_preflight
from apiscope.bookmark.prune.schema import PruneOptions
from apiscope.bookmark.schema import BookmarkEntry
from apiscope.bookmark.store import (
    entry_status,
    isolated_ids,
    layers,
    load_bookmarks,
    load_layer,
    save_layer,
)
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.lock import acquire_write_lock
from apiscope.output import Report, emit_report

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **BOOKMARK_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["bookmark.prune.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    invalid: bool = typer.Option(False, "--invalid", help=MESSAGE_TEMPLATES["bookmark.prune.help.option.invalid"]),
) -> None:
    runtime_context = resolve_context(ctx)
    try:
        lock = acquire_write_lock(runtime_context.paths.home.root)
        ctx.call_on_close(lock.release)
        options = PruneOptions(invalid=invalid)
        command_context = PruneCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        pruned = _prune(command_context)
    except ValidationError as error:
        _emit_error(runtime_context, MessageError("bookmark.prune.error.invalid_options"))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"pruned": pruned},
        ),
        output_format=runtime_context.options.output_format,
    )


# ==============================================================================
# helpers
# ==============================================================================


# delete a tombstone only from the layer that holds it, so a shadowed
# active entry in another layer is never deleted by accident
# the merged view decides isolation, while each layer decides its own status
def _prune(command_context: PruneCommandContext) -> int:
    runtime = command_context.runtime
    options = command_context.options
    merged = load_bookmarks(runtime)
    isolated = isolated_ids(merged.bookmarks)

    pruned: set[str] = set()
    for path in layers(runtime):
        data = load_layer(path)
        doomed = {
            bookmark_id
            for bookmark_id, entry in data.bookmarks.items()
            if bookmark_id in isolated and _prunable(runtime, merged.bookmarks, entry, options)
        }
        if not doomed:
            continue
        data.bookmarks = {key: value for key, value in data.bookmarks.items() if key not in doomed}
        save_layer(path, data)
        pruned.update(doomed)
    return len(pruned)


# a tombstone is prunable when it is removed itself, or invalid under --invalid
# a shadowed lower-layer entry keeps its own status, so it is never pruned here
def _prunable(
    runtime: RuntimeContext,
    entries: Mapping[str, BookmarkEntry],
    entry: BookmarkEntry,
    options: PruneOptions,
) -> bool:
    status = entry_status(runtime, entries, entry)
    if status == "removed":
        return True
    return options.invalid and status == "invalid"


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
