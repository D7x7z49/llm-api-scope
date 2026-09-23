# apiscope/content.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apiscope.cache import CacheInspection, CacheMetadata, cache_path, inspect_cache
from apiscope.source import SourceIdentity


@dataclass(frozen=True, slots=True)
class ContentSnapshot:
    source: SourceIdentity
    entry: Path
    inspection: CacheInspection

    @property
    def content(self) -> Path:
        return self.entry / "content"

    @property
    def metadata(self) -> CacheMetadata | None:
        return self.inspection.metadata


def load_content(
    cache_root: Path,
    source: SourceIdentity,
    *,
    ttl_days: int,
) -> ContentSnapshot:
    entry = cache_path(cache_root, source.canonical)
    inspection = inspect_cache(
        entry,
        ttl_days=ttl_days,
        expected_source=source.canonical,
        expected_doc_type=source.doc_type,
    )
    return ContentSnapshot(source=source, entry=entry, inspection=inspection)


__all__ = ["ContentSnapshot", "load_content"]
