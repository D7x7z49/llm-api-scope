# apiscope/errors.py

from __future__ import annotations

from collections.abc import Iterable, Mapping
from re import fullmatch
from typing import Any

from apiscope.constants import MESSAGE_TEMPLATES


class MessageError(RuntimeError):
    def __init__(self, code: str, values: Mapping[str, Any] | None = None) -> None:
        if fullmatch(r"[a-z][a-z0-9_.]*", code) is None:
            raise ValueError(MESSAGE_TEMPLATES["root.error.errors.invalid_code"])
        if values is not None and not isinstance(values, Mapping):
            raise TypeError(MESSAGE_TEMPLATES["root.error.errors.invalid_values"])
        self.code = code
        self.values = {} if values is None else dict(values)
        super().__init__(code)

    def __str__(self) -> str:
        template = MESSAGE_TEMPLATES.get(self.code)
        if template is None:
            return self.code
        try:
            return template.format(**self.values)
        except (KeyError, ValueError):
            return self.code


class MessageHintError(MessageError):
    def __init__(
        self,
        code: str,
        values: Mapping[str, Any] | None = None,
        *,
        hint_address: str,
        hint_nodes: Iterable[Mapping[str, object]],
    ) -> None:
        super().__init__(code, values)
        self.hint_address = hint_address
        self.hint_nodes = tuple(hint_nodes)
