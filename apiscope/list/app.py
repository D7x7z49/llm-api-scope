# apiscope/list/app.py

from collections.abc import Mapping
from typing import cast
from urllib.parse import quote

import typer
from pydantic import ValidationError

from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.list.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.list.context import ListCommandContext
from apiscope.list.preflight import run_preflight
from apiscope.list.schema import ListOptions, ListSelector
from apiscope.output import Report, ReportScope, emit_report
from apiscope.schema import DocumentType, RuntimeSource

_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}
_SOURCE_SAFE_CHARS = "-._~/:?#[]@!$&'()*+,;=%"

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["list.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    selector: str = typer.Argument(..., help=MESSAGE_TEMPLATES["list.help.argument.selector"]),
    limit: int | None = typer.Option(None, "--limit", min=1, help=MESSAGE_TEMPLATES["list.help.option.limit"]),
    offset: int = typer.Option(0, "--offset", min=0, help=MESSAGE_TEMPLATES["list.help.option.offset"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("list.error.runtime_context_unavailable")

    try:
        options = ListOptions(selector=cast(ListSelector, selector), limit=limit, offset=offset)
        command_context = ListCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        items = _select_sources(runtime_context.config.source, options.selector)
        window = _apply_window(items, options)
    except ValidationError as error:
        message = MessageError("list.error.invalid_selector", {"selector": selector})
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    total = len(items)
    next_offset = _next_offset(window, options, total)
    emit_report(
        Report(
            status="ok",
            scope=_scope(runtime_context),
            action=COMMAND_NAME,
            meta=_meta(options),
            data=[_report_item(name, source) for name, source in window],
            extra=_extra(len(window), total, next_offset),
        ),
        output_format=runtime_context.options.output_format,
        body=_render_window_body(window, total),
        foot=_render_foot(len(window), total, next_offset),
    )


def _select_sources(
    sources: Mapping[str, RuntimeSource],
    selector: ListSelector,
) -> list[tuple[str, RuntimeSource]]:
    selected = [(name, source) for name, source in sources.items() if selector == "all" or source.doc_type == selector]
    return sorted(selected, key=lambda item: (item[1].doc_type, item[0]))


def _apply_window(
    items: list[tuple[str, RuntimeSource]],
    options: ListOptions,
) -> list[tuple[str, RuntimeSource]]:
    end = None if options.limit is None else options.offset + options.limit
    return items[options.offset : end]


def _next_offset(
    window: list[tuple[str, RuntimeSource]],
    options: ListOptions,
    total: int,
) -> int | None:
    consumed = options.offset + len(window)
    if consumed < total:
        return consumed
    return None


def _meta(options: ListOptions) -> dict[str, object]:
    meta: dict[str, object] = {"filter": options.selector}
    if options.limit is not None:
        meta["limit"] = options.limit
    if options.offset:
        meta["offset"] = options.offset
    return meta


def _extra(count: int, total: int, next_offset: int | None) -> dict[str, int]:
    extra = {"count": count, "total": total}
    if next_offset is not None:
        extra["next"] = next_offset
    return extra


def _render_window_body(items: list[tuple[str, RuntimeSource]], total: int) -> str:
    if items:
        return _render_body(items)
    if total == 0:
        return MESSAGE_TEMPLATES["list.body.empty"]
    return MESSAGE_TEMPLATES["list.body.window_empty"]


def _render_foot(count: int, total: int, next_offset: int | None) -> str:
    if next_offset is None:
        return MESSAGE_TEMPLATES["list.foot.count"].format(count=count, total=total)
    return MESSAGE_TEMPLATES["list.foot.next"].format(count=count, total=total, next=next_offset)


def _report_item(name: str, source: RuntimeSource) -> dict[str, str]:
    return {
        "name": name,
        "type": source.doc_type,
        "source": source.doc_src,
    }


def _render_body(items: list[tuple[str, RuntimeSource]]) -> str:
    groups: dict[DocumentType, list[tuple[str, RuntimeSource]]] = {}
    for name, source in items:
        groups.setdefault(source.doc_type, []).append((name, source))

    if not groups:
        return MESSAGE_TEMPLATES["list.body.empty"]

    blocks: list[str] = []
    for doc_type, group in groups.items():
        lines = [f"[{doc_type}]"]
        lines.extend(f"- [{_format_name(name)}] {_format_source(source.doc_src)}" for name, source in group)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _format_name(value: str) -> str:
    return quote(value, safe="-._~")


def _format_source(value: str) -> str:
    return quote(value, safe=_SOURCE_SAFE_CHARS)


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
