# tests/view_lib/repo/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.repo.viewer import RepoViewer


def test_repo_viewer_hides_git_metadata(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    (content / ".git").mkdir(parents=True)
    (content / ".git" / "config").write_text("", encoding="utf-8")
    (content / "README.md").write_text("", encoding="utf-8")

    tree = RepoViewer().build(
        content,
        cache_metadata("repo", content_kind="directory", content_name=None),
    )

    assert [node.key for node in tree.indexed()] == ["README.md"]
