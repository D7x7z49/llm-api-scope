# apiscope/output.py

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from re import fullmatch
from typing import Any, Literal, TextIO
from urllib.parse import quote

from apiscope.errors import MessageError

# ==============================================================================
# types
# ==============================================================================


ReportStatus = Literal["ok", "error"]
ReportScope = Literal["home", "project"]
MessageTemplates = Mapping[str, str]


class OutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


# ==============================================================================
# errors
# ==============================================================================


class OutputError(MessageError):
    pass


# ==============================================================================
# report
# ==============================================================================


@dataclass(frozen=True, slots=True)
class Report:
    status: ReportStatus
    scope: ReportScope
    action: str
    meta: Mapping[str, Any] = field(default_factory=dict)
    code: str | None = None
    data: list[Any] | None = None
    extra: Mapping[str, Any] | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ok", "error"}:
            raise ValueError("report status must be ok or error")
        if self.scope not in {"home", "project"}:
            raise ValueError("report scope must be home or project")
        if not self.action or _is_unsafe_token(self.action):
            raise ValueError("report action must be a safe non-empty token")
        if not isinstance(self.meta, Mapping):
            raise TypeError("report meta must be a mapping")
        normalized_meta = dict(self.meta)
        for key in normalized_meta:
            _validate_field_name(key)
        object.__setattr__(self, "meta", normalized_meta)

        if self.code is not None:
            if not self.code or _is_unsafe_token(self.code):
                raise ValueError("report code must be a safe non-empty token")

        if self.status == "ok":
            if self.code is not None:
                raise ValueError("successful reports cannot contain a code")
            if self.message is not None:
                raise ValueError("successful reports cannot contain a message")
        elif self.code is None:
            raise ValueError("error reports require a code")

        if self.data is not None and not isinstance(self.data, list):
            raise TypeError("report data must be a list")
        if self.extra is not None and not isinstance(self.extra, Mapping):
            raise TypeError("report extra must be a mapping")
        if self.status == "ok":
            if (self.data is None) != (self.extra is None):
                raise ValueError("report data and extra must be provided together")
        elif self.data is not None:
            raise ValueError("error reports cannot contain read data")

        if self.data is not None:
            object.__setattr__(self, "data", list(self.data))
        if self.extra is not None:
            object.__setattr__(self, "extra", dict(self.extra))


# ==============================================================================
# rendering
# ==============================================================================


_META_FIELD_ORDER = ("name", "type", "config", "query", "filter", "count")
_EXTRA_FIELD_ORDER = ("count", "total", "next", "warnings")
_SAFE_TOKEN_PATTERN = r"^[A-Za-z0-9_.-]+$"
_SAFE_FIELD_PATTERN = r"^[a-z][a-z0-9_]*$"


def render_report(
    report: Report,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    message_templates: MessageTemplates | None = None,
    message_values: Mapping[str, Any] | None = None,
    body: str | None = None,
    foot: str | None = None,
) -> str:
    selected_format = _coerce_output_format(output_format)
    message = _resolve_message(report, message_templates, message_values)

    if selected_format is OutputFormat.JSON:
        return _render_json(report, message)
    return _render_text(report, message, body=body, foot=foot)


def emit_report(
    report: Report,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    message_templates: MessageTemplates | None = None,
    message_values: Mapping[str, Any] | None = None,
    body: str | None = None,
    foot: str | None = None,
    stream: TextIO | None = None,
) -> None:
    content = render_report(
        report,
        output_format=output_format,
        message_templates=message_templates,
        message_values=message_values,
        body=body,
        foot=foot,
    )
    target = stream if stream is not None else (sys.stderr if report.status == "error" else sys.stdout)
    print(content, file=target)


def _coerce_output_format(output_format: OutputFormat | str) -> OutputFormat:
    try:
        return OutputFormat(output_format)
    except ValueError as error:
        raise OutputError(
            "root.error.output.unsupported_format",
            {"format": repr(output_format)},
        ) from error


def _resolve_message(
    report: Report,
    message_templates: MessageTemplates | None,
    message_values: Mapping[str, Any] | None,
) -> str | None:
    if report.status == "ok":
        return None

    code = report.code
    if code is None:
        raise OutputError("root.error.output.missing_code")

    if message_templates is None:
        message = report.message
    else:
        if code not in message_templates:
            raise OutputError("root.error.output.missing_template", {"code": code})
        values = dict(report.meta)
        if message_values is not None:
            values.update(message_values)
        try:
            message = message_templates[code].format(**values)
        except (KeyError, ValueError) as error:
            raise OutputError("root.error.output.template_render_failed", {"code": code}) from error

    if message is None or not message.strip():
        raise OutputError("root.error.output.missing_message", {"code": code})
    return " ".join(message.splitlines()).strip()


def _render_text(
    report: Report,
    message: str | None,
    *,
    body: str | None,
    foot: str | None,
) -> str:
    head = _render_head(report, message)
    if report.status == "error":
        if report.extra is None:
            if body is not None or foot is not None:
                raise OutputError("root.error.output.write_sections")
            return head
        if foot is not None:
            raise OutputError("root.error.output.write_sections")
        hint = body if body is not None else _render_section_foot(report.extra)
        return f"{head}\n\n---\n\n{hint}"

    if report.data is None:
        if body is not None or foot is not None:
            raise OutputError("root.error.output.write_sections")
        return head

    rendered_body = _render_section_body(report.data) if body is None else body
    rendered_foot = _render_section_foot(report.extra) if foot is None else foot
    return f"{head}\n\n---\n\n{rendered_body}\n\n---\n\n{rendered_foot}"


def _render_head(report: Report, message: str | None) -> str:
    fields = [f"[{report.status}]", f"[scope={report.scope}]", f"[action={report.action}]"]
    if report.code is not None:
        fields.append(f"[code={report.code}]")
    fields.extend(
        f"[{key}={_format_tag_value(value)}]" for key, value in _ordered_items(report.meta, _META_FIELD_ORDER)
    )
    head = " ".join(fields)
    if message is not None:
        return f"{head}: {message}"
    return head


def _render_section_body(data: list[Any]) -> str:
    return _dump_json(data, indent=2)


def _render_section_foot(extra: Mapping[str, Any] | None) -> str:
    if extra is None:
        raise OutputError("root.error.output.missing_extra")
    return _dump_json(dict(_ordered_items(extra, _EXTRA_FIELD_ORDER)), indent=2)


def _render_json(report: Report, message: str | None) -> str:
    payload: dict[str, Any] = {
        "status": report.status,
        "scope": report.scope,
        "action": report.action,
    }
    if report.code is not None:
        payload["code"] = report.code
    payload["meta"] = dict(_ordered_items(report.meta, _META_FIELD_ORDER))
    if report.data is not None:
        payload["data"] = report.data
    if report.extra is not None:
        payload["extra"] = dict(_ordered_items(report.extra, _EXTRA_FIELD_ORDER))
    if message is not None:
        payload["message"] = message
    return _dump_json(payload)


# ==============================================================================
# value helpers
# ==============================================================================


def _ordered_items(values: Mapping[str, Any], preferred: tuple[str, ...]) -> list[tuple[str, Any]]:
    priority = {key: index for index, key in enumerate(preferred)}
    return sorted(values.items(), key=lambda item: (priority.get(item[0], len(preferred)), item[0]))


def _validate_field_name(name: str) -> None:
    if not isinstance(name, str) or fullmatch(_SAFE_FIELD_PATTERN, name) is None:
        raise ValueError(f"report field name is unsafe {name!r}")


def _is_unsafe_token(value: str) -> bool:
    return fullmatch(_SAFE_TOKEN_PATTERN, value) is None


def _format_tag_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return quote(value, safe="-._~")
    return quote(_dump_json(value), safe="-._~")


def _dump_json(value: Any, *, indent: int | None = None) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError) as error:
        raise OutputError("root.error.output.serialization_failed") from error
