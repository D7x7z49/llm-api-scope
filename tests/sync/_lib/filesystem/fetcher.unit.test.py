# tests/sync/_lib/filesystem/fetcher.unit.test.py
from pathlib import Path

import pytest

from apiscope.source import parse_source
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.filesystem.fetcher import FilesystemFetcher


def test_filesystem_fetcher_copies_a_file_and_returns_its_digest(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello\n", encoding="utf-8")
    destination = tmp_path / "staging"
    parsed = parse_source("filesystem", str(source), base_dir=tmp_path)

    result = FilesystemFetcher().fetch(parsed, destination=destination)

    assert result.content_kind == "file"
    assert result.content_name == "source.txt"
    assert (destination / "content" / "source.txt").read_text(encoding="utf-8") == "hello\n"
    assert result.content_digest


def test_filesystem_fetcher_copies_a_directory_tree(tmp_path: Path) -> None:
    source = tmp_path / "docs"
    (source / "nested").mkdir(parents=True)
    (source / "index.txt").write_text("index\n", encoding="utf-8")
    (source / "nested" / "detail.txt").write_text("detail\n", encoding="utf-8")
    destination = tmp_path / "staging"
    parsed = parse_source("filesystem", str(source), base_dir=tmp_path)

    result = FilesystemFetcher().fetch(parsed, destination=destination)

    assert result.content_kind == "directory"
    assert result.content_name is None
    assert (destination / "content" / "index.txt").read_text(encoding="utf-8") == "index\n"
    assert (destination / "content" / "nested" / "detail.txt").read_text(encoding="utf-8") == "detail\n"
    assert result.content_digest


def test_filesystem_fetcher_reports_a_missing_path(tmp_path: Path) -> None:
    source = tmp_path / "missing.txt"
    destination = tmp_path / "staging"
    parsed = parse_source("filesystem", str(source), base_dir=tmp_path)

    with pytest.raises(SourceFetchError) as raised:
        FilesystemFetcher().fetch(parsed, destination=destination)

    assert raised.value.reason_code == "fetch.source_path_missing"
    assert raised.value.values == {"path": str(source)}
