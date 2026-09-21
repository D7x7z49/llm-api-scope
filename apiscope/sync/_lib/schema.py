# apiscope/sync/_lib/schema.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from apiscope.schema import DocumentType

ContentKind = Literal["file", "directory"]


@dataclass(frozen=True, slots=True)
class LocalSource:
    path: Path


@dataclass(frozen=True, slots=True)
class RemoteSource:
    url: str


SourceLocation = LocalSource | RemoteSource


@dataclass(frozen=True, slots=True)
class ParsedSource:
    doc_type: DocumentType
    original: str
    canonical: str
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class FetchResult:
    fetched_at: datetime
    content_kind: ContentKind
    content_name: str | None
    content_digest: str
