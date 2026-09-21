# apiscope/view/_lib/errors.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ViewReasonError(ValueError):
    def __init__(self, reason_code: str, values: Mapping[str, Any] | None = None) -> None:
        self.reason_code = reason_code
        self.values = {} if values is None else dict(values)
        super().__init__(reason_code)


class ViewSourceError(ViewReasonError):
    pass


class ViewProjectionError(ViewReasonError):
    pass
