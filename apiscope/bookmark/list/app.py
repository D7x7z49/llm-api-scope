# apiscope/bookmark/list/app.py

import typer
from pydantic import ValidationError

from apiscope.bookmark.constants import MESSAGE_TEMPLATES as BOOKMARK_MESSAGE_TEMPLATES
from apiscope.bookmark.context import resolve_context
from apiscope.bookmark.list.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.bookmark.list.context import ListCommandContext
from apiscope.bookmark.list.preflight import run_preflight
from apiscope.bookmark.list.schema import ListOptions
from apiscope.bookmark.schema import BookmarkEntry, BookmarkFile
from apiscope.bookmark.store import entry_status, load_bookmarks
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **BOOKMARK_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["bookmark.list.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    group: str | None = typer.Argument(None, help=MESSAGE_TEMPLATES["bookmark.list.help.argument.group"]),
) -> None:
    runtime_context = resolve_context(ctx)
    try:
        options = ListOptions(group=group)
        command_context = ListCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        data = load_bookmarks(runtime_context)
        entries = _select(data, options.group)
    except ValidationError as error:
        _emit_error(runtime_context, MessageError("bookmark.list.error.group_not_found", {"id": group}))
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    rows = [_row(runtime_context, data, entry) for entry in entries]
    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            data=rows,
            extra={"count": len(rows)},
        ),
        output_format=runtime_context.options.output_format,
        body=_render_body(rows),
    )


# ==============================================================================
# helpers
# ==============================================================================


def _select(data: BookmarkFile, group: str | None) -> list[BookmarkEntry]:
    if group is None:
        return [data.bookmarks[key] for key in sorted(data.bookmarks)]
    entry = data.bookmarks.get(group)
    if entry is None or entry.mode != "group":
        raise MessageError("bookmark.list.error.group_not_found", {"id": group})
    return [data.bookmarks[member] for member in entry.members if member in data.bookmarks]


def _row(runtime: RuntimeContext, data: BookmarkFile, entry: BookmarkEntry) -> dict[str, str]:
    return {
        "id": entry.id,
        "mode": entry.mode,
        "target": entry.target,
        "status": entry_status(runtime, data.bookmarks, entry),
    }


def _render_body(rows: list[dict[str, str]]) -> str:
    if not rows:
        return MESSAGE_TEMPLATES["bookmark.list.body.empty"]
    return "\n".join(f"- [{row['id']}] {row['mode']} {row['target']} ({row['status']})" for row in rows)


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
