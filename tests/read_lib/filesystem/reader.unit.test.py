# tests/read_lib/filesystem/reader.unit.test.py
from collections.abc import Callable
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.view_lib.schema import IndexedNode


def test_filesystem_reader_returns_utf8_markdown(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "guide.md").write_text("guide\n", encoding="utf-8")
    metadata = cache_metadata("filesystem", content_kind="directory")

    result = FilesystemReader().read(content, metadata, indexed_node("guide.md"))

    assert result.kind == "markdown"
    assert result.content == "guide\n"
    assert result.encoding == "utf-8"
    assert result.size == 6


def test_filesystem_reader_reports_binary_size(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "blob.bin").write_bytes(b"\x00\xff")
    metadata = cache_metadata("filesystem", content_kind="directory")

    result = FilesystemReader().read(content, metadata, indexed_node("blob.bin"))

    assert result.kind == "binary"
    assert result.content is None
    assert result.size == 2


def test_filesystem_reader_rejects_paths_outside_content(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (tmp_path / "secret").write_text("secret", encoding="utf-8")
    metadata = cache_metadata("filesystem", content_kind="directory")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_invalid"):
        FilesystemReader().read(content, metadata, indexed_node("../secret"))
