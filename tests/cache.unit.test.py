# tests/cache.unit.test.py
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apiscope import cache as cache_module
from apiscope.cache import CACHE_FORMAT_VERSION, CacheMetadata, cache_path, inspect_cache, staging_cache, write_metadata
from apiscope.source import parse_source
from apiscope.sync._lib.filesystem.fetcher import FilesystemFetcher


def test_cache_promotes_metadata_and_content_atomically(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello\n", encoding="utf-8")
    parsed = parse_source("filesystem", str(source), base_dir=tmp_path)
    cache_root = tmp_path / "cache"

    with staging_cache(cache_root, parsed.canonical) as staging:
        result = FilesystemFetcher().fetch(parsed, destination=staging)
        write_metadata(
            staging,
            CacheMetadata(
                format_version=CACHE_FORMAT_VERSION,
                doc_type=parsed.doc_type,
                source=parsed.canonical,
                fetched_at=result.fetched_at,
                content_kind=result.content_kind,
                content_name=result.content_name,
                content_digest=result.content_digest,
            ),
        )

    entry = cache_path(cache_root, parsed.canonical)
    inspection = inspect_cache(entry, ttl_days=7)
    assert inspection.state == "fresh"
    assert (entry / "metadata.json").exists()
    assert (entry / "content" / "source.txt").exists()


def test_cache_rejects_an_unknown_format_version(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    entry = cache_path(cache_root, "file:///source.txt")
    (entry / "content").mkdir(parents=True)
    (entry / "content" / "source.txt").write_text("hello\n", encoding="utf-8")
    write_metadata(
        entry,
        CacheMetadata(
            format_version="2",
            doc_type="filesystem",
            source="file:///source.txt",
            fetched_at=datetime.now(timezone.utc),
            content_kind="file",
            content_name="source.txt",
            content_digest="digest",
        ),
    )

    inspection = inspect_cache(entry, ttl_days=7)

    assert inspection.state == "invalid"


def test_cache_rejects_metadata_for_another_source(
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    entry = cache_path(cache_root, "file:///source.txt")
    (entry / "content").mkdir(parents=True)
    (entry / "content" / "source.txt").write_text("hello\n", encoding="utf-8")
    write_metadata(
        entry,
        CacheMetadata(
            format_version=CACHE_FORMAT_VERSION,
            doc_type="filesystem",
            source="file:///source.txt",
            fetched_at=datetime.now(timezone.utc),
            content_kind="file",
            content_name="source.txt",
            content_digest="digest",
        ),
    )

    inspection = inspect_cache(
        entry,
        ttl_days=7,
        expected_source="file:///other.txt",
        expected_doc_type="repo",
    )

    assert inspection.state == "invalid"


def test_staging_cache_restores_the_previous_entry_after_promotion_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_root = tmp_path / "cache"
    canonical_source = "file:///source.txt"
    entry = cache_path(cache_root, canonical_source)
    entry.mkdir(parents=True)
    (entry / "sentinel.txt").write_text("old\n", encoding="utf-8")
    real_replace = cache_module.os.replace
    staging_path: Path | None = None

    def fail_staging_promotion(source: str | Path, target: str | Path) -> None:
        if staging_path is not None and Path(source) == staging_path:
            raise OSError("promotion failed")
        real_replace(source, target)

    monkeypatch.setattr(cache_module.os, "replace", fail_staging_promotion)

    with pytest.raises(OSError, match="promotion failed"):
        with staging_cache(cache_root, canonical_source) as staging:
            staging_path = staging
            (staging / "content").mkdir()
            (staging / "content" / "new.txt").write_text("new\n", encoding="utf-8")

    assert (entry / "sentinel.txt").read_text(encoding="utf-8") == "old\n"
    assert not any(path.name.endswith(".backup") for path in cache_root.iterdir())
    assert not any(path.name.startswith(f".{entry.name}.") for path in cache_root.iterdir())
