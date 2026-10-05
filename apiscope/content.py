# apiscope/content.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apiscope.cache import CacheInspection, CacheMetadata, cache_path, inspect_cache, source_digest
from apiscope.source import Source, cache_identity


@dataclass(frozen=True, slots=True)
class ContentSnapshot:
    source: Source
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
    source: Source,
    *,
    base_dir: Path,
    ttl_days: int,
) -> ContentSnapshot:
    identity = cache_identity(source, base_dir=base_dir)
    entry = cache_path(cache_root, identity)
    inspection = inspect_cache(
        entry,
        ttl_days=ttl_days,
        expected_source=source.original,
        expected_doc_type=source.doc_type,
        expected_digest=source_digest(identity),
    )
    return ContentSnapshot(source=source, entry=entry, inspection=inspection)


__all__ = ["ContentSnapshot", "load_content"]
