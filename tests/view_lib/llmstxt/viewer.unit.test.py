# tests/view_lib/llmstxt/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.llmstxt.viewer import LlmstxtViewer


def test_llmstxt_viewer_builds_a_directory_tree(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    (content / "guide").mkdir(parents=True)
    (content / "guide" / "intro.md").write_text("intro\n", encoding="utf-8")
    (content / "llms.txt").write_text("# Docs\n", encoding="utf-8")

    tree = LlmstxtViewer().build(
        content,
        cache_metadata("llmstxt", content_kind="directory", content_name=None),
    )

    assert [(node.index, node.key) for node in tree.indexed()] == [
        ("1", "guide"),
        ("1.1", "intro.md"),
        ("2", "llms.txt"),
    ]
