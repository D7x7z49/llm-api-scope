# tests/sync/_lib/cache.unit.test.py
from pathlib import Path

import pytest

from apiscope.sync._lib import cache as cache_module
from apiscope.sync._lib.cache import cache_path, inspect_cache, staging_cache, write_metadata
from apiscope.sync._lib.filesystem.fetcher import FilesystemFetcher
from apiscope.sync._lib.filesystem.parser import FilesystemParser


def test_cache_promotes_metadata_and_content_atomically(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello\n", encoding="utf-8")
    parsed = FilesystemParser().parse(str(source), base_dir=tmp_path)
    cache_root = tmp_path / "cache"

    with staging_cache(cache_root, parsed.canonical) as staging:
        result = FilesystemFetcher().fetch(parsed, destination=staging)
        write_metadata(staging, parsed, result)

    entry = cache_path(cache_root, parsed.canonical)
    inspection = inspect_cache(entry, ttl_days=7)
    assert inspection.state == "fresh"
    assert (entry / "metadata.json").exists()
    assert (entry / "content" / "source.txt").exists()


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
