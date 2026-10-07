# apiscope/bookmark/remove/app.py

import typer
from pydantic import ValidationError

from apiscope.bookmark.constants import MESSAGE_TEMPLATES as BOOKMARK_MESSAGE_TEMPLATES
from apiscope.bookmark.context import resolve_context
from apiscope.bookmark.remove.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.bookmark.remove.context import RemoveCommandContext
from apiscope.bookmark.remove.preflight import run_preflight
from apiscope.bookmark.remove.schema import RemoveOptions
from apiscope.bookmark.store import ensure_bookmarks, layers, load_layer, save_layer
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
    help=MESSAGE_TEMPLATES["bookmark.remove.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    bookmark_id: str = typer.Argument(..., metavar="ID", help=MESSAGE_TEMPLATES["bookmark.remove.help.argument.id"]),
) -> None:
    runtime_context = resolve_context(ctx)
    try:
        lock = acquire_write_lock(runtime_context.paths.home.root)
        ctx.call_on_close(lock.release)
        options = RemoveOptions(id=bookmark_id)
        command_context = RemoveCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        _remove(command_context)
    except ValidationError as error:
        _emit_error(runtime_context, MessageError("bookmark.remove.error.id_not_found", {"id": bookmark_id}))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta={"id": options.id},
        ),
        output_format=runtime_context.options.output_format,
    )


# ==============================================================================
# helpers
# ==============================================================================


def _remove(command_context: RemoveCommandContext) -> None:
    runtime = command_context.runtime
    options = command_context.options
    ensure_bookmarks(runtime)
    for path in layers(runtime):
        data = load_layer(path)
        entry = data.bookmarks.get(options.id)
        if entry is None:
            continue
        if entry.removed:
            raise MessageError("bookmark.remove.error.already_removed", {"id": options.id})

        # keep the stored field set unchanged, so a non-group entry
        # never gains an empty members field just because it was removed
        updated = entry.model_copy(update={"removed": True})
        data.bookmarks = {**data.bookmarks, options.id: updated}
        save_layer(path, data)
        return
    raise MessageError("bookmark.remove.error.id_not_found", {"id": options.id})


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
