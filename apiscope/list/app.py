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
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    selector: str = typer.Argument(..., help=MESSAGE_TEMPLATES["list.help.argument.selector"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("list.error.runtime_context_unavailable")

    try:
        options = ListOptions(selector=cast(ListSelector, selector))
        command_context = ListCommandContext(runtime=runtime_context, options=options)
        run_preflight(command_context)
        items = _select_sources(runtime_context.config.source, options.selector)
    except ValidationError as error:
        message = MessageError("list.error.invalid_selector", {"selector": selector})
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
            meta={"filter": options.selector},
            data=[_report_item(name, source) for name, source in items],
            extra={"count": len(items)},
        ),
        output_format=runtime_context.options.output_format,
        body=_render_body(items),
        foot=MESSAGE_TEMPLATES["list.foot.count"].format(count=len(items)),
    )


def _select_sources(
    sources: Mapping[str, RuntimeSource],
    selector: ListSelector,
) -> list[tuple[str, RuntimeSource]]:
    selected = [(name, source) for name, source in sources.items() if selector == "all" or source.doc_type == selector]
    return sorted(selected, key=lambda item: (item[1].doc_type, item[0]))


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
