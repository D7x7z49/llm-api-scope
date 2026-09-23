# apiscope/view_lib/errors.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ProjectionError(ValueError):
    def __init__(self, reason_code: str, values: Mapping[str, Any] | None = None) -> None:
        self.reason_code = reason_code
        self.values = {} if values is None else dict(values)
        super().__init__(reason_code)


__all__ = ["ProjectionError"]
