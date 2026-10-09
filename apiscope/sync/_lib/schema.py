# apiscope/sync/_lib/schema.py
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias

from apiscope.source import LocalLocation, RemoteLocation, Source, SourceLocation

ContentKind = Literal["file", "directory"]
ParsedSource: TypeAlias = Source

__all__ = ["ContentKind", "FetchResult", "LocalLocation", "ParsedSource", "RemoteLocation", "SourceLocation"]


@dataclass(frozen=True, slots=True)
class FetchResult:
    fetched_at: datetime
    content_kind: ContentKind
    content_name: str | None
    content_digest: str
    manifest: Mapping[str, str] | None = None
