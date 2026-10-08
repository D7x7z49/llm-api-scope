# tests/read_lib/repo/reader.unit.test.py
from collections.abc import Callable
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.repo.reader import RepoReader
from apiscope.view_lib.schema import IndexedNode


def test_repo_reader_rejects_an_ordinary_directory_node(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    (content / "docs").mkdir(parents=True)
    metadata = cache_metadata("filesystem", content_kind="directory")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_leaf"):
        RepoReader().read(content, metadata, indexed_node("docs", node_type="ordinary"))
