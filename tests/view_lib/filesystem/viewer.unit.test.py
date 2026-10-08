# tests/view_lib/filesystem/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.filesystem.viewer import FilesystemViewer


def test_filesystem_viewer_builds_a_sorted_directory_tree(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    (content / "z").mkdir(parents=True)
    (content / "a").mkdir()
    (content / "z" / "last.md").write_text("", encoding="utf-8")
    (content / "a" / "first.md").write_text("", encoding="utf-8")

    tree = FilesystemViewer().build(
        content,
        cache_metadata("filesystem", content_kind="directory", content_name=None),
    )

    assert [(node.index, node.key) for node in tree.indexed()] == [
        ("1", "a"),
        ("1.1", "first.md"),
        ("2", "z"),
        ("2.1", "last.md"),
    ]
    nodes = {node.index: node for node in tree.indexed()}
    assert nodes["1"].node_type == "ordinary"
    assert nodes["1.1"].node_type == "leaf"


def test_filesystem_viewer_keeps_empty_directories_ordinary(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    (content / "empty").mkdir(parents=True)

    tree = FilesystemViewer().build(
        content,
        cache_metadata("filesystem", content_kind="directory", content_name=None),
    )

    assert tree.indexed()[0].node_type == "ordinary"


def test_filesystem_viewer_does_not_follow_a_self_link(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "readme.md").write_text("", encoding="utf-8")
    (content / "self").symlink_to(content)

    tree = FilesystemViewer().build(
        content,
        cache_metadata("filesystem", content_kind="directory", content_name=None),
    )

    assert [(node.index, node.key, node.node_type) for node in tree.indexed()] == [
        ("1", "readme.md", "leaf"),
        ("2", "self", "leaf"),
    ]


def test_filesystem_viewer_marks_an_outside_link_as_a_leaf(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("", encoding="utf-8")
    content = tmp_path / "content"
    content.mkdir()
    (content / "link").symlink_to(outside)

    tree = FilesystemViewer().build(
        content,
        cache_metadata("filesystem", content_kind="directory", content_name=None),
    )

    assert [(node.index, node.key, node.node_type) for node in tree.indexed()] == [("1", "link", "leaf")]
