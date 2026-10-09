# tests/view_lib/llmstxt/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.llmstxt.viewer import LlmstxtViewer


def test_llmstxt_viewer_builds_a_route_tree(
    tmp_path: Path,
    expected: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (tmp_path / "manifest.json").write_text(expected("llmstxt/manifest.json"), encoding="utf-8")

    tree = LlmstxtViewer().build(
        content,
        cache_metadata("llmstxt", content_kind="directory", content_name=None),
    )

    assert [(node.index, node.key) for node in tree.indexed()] == [
        ("1", "guide"),
        ("1.1", "index"),
        ("1.2", "intro.md"),
        ("2", "llms.txt"),
    ]
    assert not tree.resolve("guide").is_leaf
    assert tree.resolve("guide/index").is_leaf
    assert tree.resolve("guide/index").source_target
