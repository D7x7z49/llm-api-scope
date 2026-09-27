# apiscope/read_lib/errors.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from apiscope.read_lib.constants import ReadReason


class ReadError(ValueError):
    def __init__(self, reason: ReadReason, values: Mapping[str, Any] | None = None) -> None:
        self.code = reason.value
        self.values = {} if values is None else dict(values)
        super().__init__(self.code)
