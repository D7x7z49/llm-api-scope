# tests/view_lib/tree.unit.test.py
import pytest

from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.schema import TreeNode
from apiscope.view_lib.tree import SourceTree


def test_index_width_is_selected_per_parent() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(
                key="docs",
                path="docs",
                children=tuple(TreeNode(key=f"page-{index}") for index in range(10)),
            ),
            TreeNode(key="readme.md", path="readme.md"),
        ),
        normalize_path=lambda value: "" if value == "." else value,
    )

    assert [node.index for node in tree.indexed()] == [
        "1",
        "1.01",
        "1.02",
        "1.03",
        "1.04",
        "1.05",
        "1.06",
        "1.07",
        "1.08",
        "1.09",
        "1.10",
        "2",
    ]


def test_resolve_finds_a_stable_source_path() -> None:
    tree = SourceTree(
        roots=(TreeNode(key="readme.md", path="docs/readme.md"),),
        normalize_path=lambda value: value,
    )

    node = tree.resolve("docs/readme.md")

    assert node.path == "docs/readme.md"
    assert node.index == "1"


def test_resolve_index_selects_the_view_node() -> None:
    tree = SourceTree(
        roots=(TreeNode(key="docs", path="docs", children=(TreeNode(key="guide.md", path="docs/guide.md"),)),),
        normalize_path=lambda value: value,
    )

    node = tree.resolve_index("1.1")

    assert node.path == "docs/guide.md"
    assert node.is_leaf


def test_missing_route_reports_longest_prefix_and_available_children() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(
                key="docs",
                path="docs",
                children=(
                    TreeNode(
                        key="api",
                        path="docs/api",
                        node_type="ordinary",
                        children=(TreeNode(key="guide.md", path="docs/api/guide.md"),),
                    ),
                ),
            ),
        ),
        normalize_path=lambda value: value,
    )

    with pytest.raises(ProjectionError) as caught:
        tree.select("docs/api/missing.md")

    assert caught.value.reason_code == ProjectionReason.PATH_NOT_FOUND
    assert caught.value.values == {
        "path": "docs/api/missing.md",
        "prefix": "docs/api",
        "nodes": [{"index": "1", "key": "guide.md", "node_type": "leaf"}],
    }


def test_ambiguous_route_lists_candidates_and_indexes() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(key="first", path="same"),
            TreeNode(key="second", path="same"),
        ),
        normalize_path=lambda value: value,
    )

    with pytest.raises(ProjectionError) as caught:
        tree.select("same")

    assert caught.value.reason_code == ProjectionReason.PATH_AMBIGUOUS
    assert caught.value.values["prefix"] == "."
    assert caught.value.values["routes"] == [
        {"index": "1", "route": "same", "label": "first", "node_type": "leaf"},
        {"index": "2", "route": "same", "label": "second", "node_type": "leaf"},
    ]


def test_empty_ordinary_node_is_not_a_leaf() -> None:
    tree = SourceTree(
        roots=(TreeNode(key="empty", path="empty", node_type="ordinary"),),
        normalize_path=lambda value: value,
    )

    assert not tree.resolve_index("1").is_leaf
    assert tree.children_of(tree.resolve_index("1")) == ()


def test_select_relays_out_indexes_for_a_partial_scope() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(
                key="docs",
                path="docs",
                children=(
                    TreeNode(key="api.md", path="docs/api.md"),
                    TreeNode(key="guide.md", path="docs/guide.md"),
                ),
            ),
            TreeNode(key="readme.md", path="readme.md"),
        ),
        normalize_path=lambda value: "" if value == "." else value,
    )

    selected = tree.select("docs")

    assert [(node.index, node.key) for node in selected] == [
        ("1", "docs"),
        ("1.1", "api.md"),
        ("1.2", "guide.md"),
    ]


def test_select_relays_out_indexes_below_a_leaf_scope() -> None:
    tree = SourceTree(
        roots=(TreeNode(key="docs", path="docs", children=(TreeNode(key="guide.md", path="docs/guide.md"),)),),
        normalize_path=lambda value: "" if value == "." else value,
    )

    selected = tree.select("docs/guide.md")

    assert [(node.index, node.key) for node in selected] == [("1", "guide.md")]


def test_tree_rejects_duplicate_sibling_keys() -> None:
    with pytest.raises(ProjectionError) as caught:
        SourceTree(
            roots=(TreeNode(key="same", path="a"), TreeNode(key="same", path="b")),
            normalize_path=lambda value: value,
        )

    assert caught.value.reason_code == ProjectionReason.DUPLICATE_KEY
    assert caught.value.values == {"key": "same"}
