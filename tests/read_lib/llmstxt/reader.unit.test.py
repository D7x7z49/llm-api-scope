# tests/read_lib/llmstxt/reader.unit.test.py
from collections.abc import Callable
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.llmstxt.reader import LlmstxtReader
from apiscope.view_lib.schema import IndexedNode


def test_llmstxt_reader_reads_a_body(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "abc123").write_text("# Guide\n", encoding="utf-8")

    result = LlmstxtReader().read(
        content,
        cache_metadata("llmstxt", content_kind="directory", content_name=None),
        indexed_node("guide/intro.md", source_target="abc123"),
    )

    assert result.kind == "markdown"
    assert result.content == "# Guide\n"
    assert result.media_type == "text/markdown"
    assert "retrieval" not in result.as_extra("fresh")


def test_llmstxt_reader_reports_a_missing_body(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_invalid"):
        LlmstxtReader().read(
            content,
            cache_metadata("llmstxt", content_kind="directory", content_name=None),
            indexed_node("guide.md", source_target="missing"),
        )


def test_llmstxt_reader_reports_a_leaf_without_a_body(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_found"):
        LlmstxtReader().read(
            content,
            cache_metadata("llmstxt", content_kind="directory", content_name=None),
            indexed_node("guide.md"),
        )


def test_llmstxt_reader_rejects_an_ordinary_target(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_leaf"):
        LlmstxtReader().read(
            content,
            cache_metadata("llmstxt", content_kind="directory", content_name=None),
            indexed_node("guide", node_type="ordinary"),
        )
