# tests/cache.unit.test.py
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apiscope import cache as cache_module
from apiscope.cache import (
    CACHE_CONTENT_DIRECTORY,
    CACHE_DIGEST_MIN_LENGTH,
    CACHE_FORMAT_VERSION,
    CacheMetadata,
    build_manifest,
    cache_path,
    inspect_cache,
    staging_cache,
    write_manifest,
    write_metadata,
)
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
                source_digest=cache_module.source_digest(parsed.canonical),
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
            source_digest="digest",
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
            source_digest="digest",
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


def test_manifest_lists_files_and_directories(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "api").mkdir(parents=True)
    (content / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (content / "README.md").write_text("readme\n", encoding="utf-8")

    manifest = build_manifest(content)

    assert set(manifest) == {".", "README.md", "api", "api/overview.md"}
    assert manifest["README.md"] != manifest["api"]


def test_cache_rejects_a_directory_entry_without_a_manifest(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    entry = cache_path(cache_root, "file:///docs")
    (entry / CACHE_CONTENT_DIRECTORY / "api").mkdir(parents=True)
    (entry / CACHE_CONTENT_DIRECTORY / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    write_metadata(
        entry,
        CacheMetadata(
            format_version=CACHE_FORMAT_VERSION,
            doc_type="filesystem",
            source="file:///docs",
            source_digest="digest",
            fetched_at=datetime.now(timezone.utc),
            content_kind="directory",
            content_name=None,
            content_digest="digest",
        ),
    )

    inspection = inspect_cache(entry, ttl_days=7)

    assert inspection.state == "invalid"


def test_cache_accepts_a_directory_entry_with_a_manifest(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    entry = cache_path(cache_root, "file:///docs")
    content = entry / CACHE_CONTENT_DIRECTORY
    (content / "api").mkdir(parents=True)
    (content / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    write_manifest(entry, build_manifest(content))
    write_metadata(
        entry,
        CacheMetadata(
            format_version=CACHE_FORMAT_VERSION,
            doc_type="filesystem",
            source="file:///docs",
            source_digest="digest",
            fetched_at=datetime.now(timezone.utc),
            content_kind="directory",
            content_name=None,
            content_digest="digest",
        ),
    )

    inspection = inspect_cache(entry, ttl_days=7)

    assert inspection.state == "fresh"


def test_cache_path_uses_a_short_source_digest(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    canonical = "file:///source.txt"

    entry = cache_path(cache_root, canonical)

    assert entry.name == cache_module.source_digest(canonical)[:CACHE_DIGEST_MIN_LENGTH]
    assert len(entry.name) == CACHE_DIGEST_MIN_LENGTH


def test_cache_names_extend_a_shared_prefix() -> None:
    first = "a" * CACHE_DIGEST_MIN_LENGTH + "1" + "0" * 50
    second = "a" * CACHE_DIGEST_MIN_LENGTH + "2" + "0" * 50

    names = cache_module._assign_cache_names([first, second])

    assert names[first] == first[: CACHE_DIGEST_MIN_LENGTH + 1]
    assert names[second] == second[: CACHE_DIGEST_MIN_LENGTH + 1]


def test_cache_entry_keeps_the_full_source_digest(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello\n", encoding="utf-8")
    parsed = parse_source("filesystem", str(source), base_dir=tmp_path)
    cache_root = tmp_path / "cache"
    digest = cache_module.source_digest(parsed.canonical)

    with staging_cache(cache_root, parsed.canonical) as staging:
        result = FilesystemFetcher().fetch(parsed, destination=staging)
        write_metadata(
            staging,
            CacheMetadata(
                format_version=CACHE_FORMAT_VERSION,
                doc_type=parsed.doc_type,
                source=parsed.canonical,
                source_digest=digest,
                fetched_at=result.fetched_at,
                content_kind=result.content_kind,
                content_name=result.content_name,
                content_digest=result.content_digest,
            ),
        )

    entry = cache_path(cache_root, parsed.canonical)
    metadata = json.loads((entry / "metadata.json").read_text(encoding="utf-8"))

    assert len(entry.name) == CACHE_DIGEST_MIN_LENGTH
    assert metadata["source_digest"] == digest
    assert metadata["content_digest"] != metadata["source_digest"]


def test_cache_extends_entries_that_share_a_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_root = tmp_path / "cache"
    digests = {
        "file:///a": "a" * CACHE_DIGEST_MIN_LENGTH + "1" + "0" * 56,
        "file:///b": "a" * CACHE_DIGEST_MIN_LENGTH + "2" + "0" * 56,
    }
    monkeypatch.setattr(cache_module, "source_digest", lambda value: digests[value])

    for canonical in ("file:///a", "file:///b"):
        entry = cache_module._prepare_cache_entry(cache_root, canonical)
        (entry / "content").mkdir(parents=True)
        (entry / "content" / "doc.txt").write_text("x\n", encoding="utf-8")
        write_metadata(
            entry,
            CacheMetadata(
                format_version=CACHE_FORMAT_VERSION,
                doc_type="filesystem",
                source=canonical,
                source_digest=digests[canonical],
                fetched_at=datetime.now(timezone.utc),
                content_kind="file",
                content_name="doc.txt",
                content_digest="digest",
            ),
        )

    assert (cache_root / digests["file:///a"][: CACHE_DIGEST_MIN_LENGTH + 1]).is_dir()
    assert (cache_root / digests["file:///b"][: CACHE_DIGEST_MIN_LENGTH + 1]).is_dir()


def test_cache_rejects_metadata_with_another_source_digest(tmp_path: Path) -> None:
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
            source_digest="0" * 64,
            fetched_at=datetime.now(timezone.utc),
            content_kind="file",
            content_name="source.txt",
            content_digest="digest",
        ),
    )

    inspection = inspect_cache(entry, ttl_days=7, expected_digest="f" * 64)

    assert inspection.state == "invalid"
