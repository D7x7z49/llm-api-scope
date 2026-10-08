# apiscope/validation.py

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from pydantic import ValidationError

_VALUE_LIMIT: Final = 48


def describe(error: ValidationError, labels: Mapping[str, str] | None = None) -> str:
    """Render a validation error as a short, actionable clause.

    Each finding names the field, the rule, and the observed value, so the
    caller can recover without trial and error.
    """
    names = {} if labels is None else labels
    return "; ".join(_finding(item, names) for item in error.errors())


def _finding(item: Mapping[str, Any], labels: Mapping[str, str]) -> str:
    kind = str(item.get("type", "value_error"))
    ctx = item.get("ctx") or {}
    field = _field(item.get("loc", ()), labels)
    value = item.get("input")

    if kind == "missing":
        return f"[{field}] is required"
    if kind == "extra_forbidden":
        return f"[{field}] is not an accepted option"
    if kind == "string_too_short":
        return f"[{field}] must be at least {ctx.get('min_length')} characters, but {_size(value)}"
    if kind == "string_too_long":
        return f"[{field}] must be at most {ctx.get('max_length')} characters, but {_size(value)}"
    if kind == "string_pattern_mismatch":
        return f"[{field}] must match the pattern {ctx.get('pattern')}, but [{_short(value)}] was given"
    if kind in {"int_parsing", "int_type", "int_from_float"}:
        return f"[{field}] must be an integer, but [{_short(value)}] was given"
    if kind == "greater_than_equal":
        return f"[{field}] must be at least {ctx.get('ge')}, but [{_short(value)}] was given"
    if kind == "greater_than":
        return f"[{field}] must be greater than {ctx.get('gt')}, but [{_short(value)}] was given"
    if kind == "less_than_equal":
        return f"[{field}] must be at most {ctx.get('le')}, but [{_short(value)}] was given"
    if kind == "less_than":
        return f"[{field}] must be less than {ctx.get('lt')}, but [{_short(value)}] was given"
    if kind in {"enum", "literal_error"}:
        return f"[{field}] must be one of {ctx.get('expected')}, but [{_short(value)}] was given"
    if kind in {"string_type", "str_type"}:
        return f"[{field}] must be text, but [{_short(value)}] was given"
    return f"[{field}] {str(item.get('msg', 'is invalid')).lower()}"


def _field(loc: Sequence[Any], labels: Mapping[str, str]) -> str:
    name = str(loc[-1]) if loc else "value"
    return labels.get(name, name)


def _size(value: Any) -> str:
    if isinstance(value, str):
        return f"{len(value)} characters were given"
    return "a value of the wrong size was given"


def _short(value: Any) -> str:
    text = "" if value is None else str(value)
    if len(text) <= _VALUE_LIMIT:
        return text
    return f"{text[:_VALUE_LIMIT]}..."


__all__ = ["describe"]
