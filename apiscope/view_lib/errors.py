# apiscope/view_lib/errors.py
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from apiscope.errors import MessageError


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


class ProjectionError(ValueError):
    def __init__(self, reason_code: str, values: Mapping[str, Any] | None = None) -> None:
        self.reason_code = reason_code
        self.values = {} if values is None else dict(values)
        super().__init__(reason_code)


__all__ = ["MessageHintError", "ProjectionError"]
