# apiscope/sync/_lib/schema.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias

from apiscope.source import LocalSource, RemoteSource, SourceIdentity, SourceLocation

ContentKind = Literal["file", "directory"]
ParsedSource: TypeAlias = SourceIdentity

__all__ = ["ContentKind", "FetchResult", "LocalSource", "ParsedSource", "RemoteSource", "SourceLocation"]


@dataclass(frozen=True, slots=True)
class FetchResult:
    fetched_at: datetime
    content_kind: ContentKind
    content_name: str | None
    content_digest: str
