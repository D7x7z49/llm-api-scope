# tests/view_lib/tree.unit.test.py
from apiscope.view_lib.tree import SourceTree, TreeNode


def test_index_width_is_selected_per_parent() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(
                value="docs",
                path="docs",
                children=tuple(TreeNode(value=f"page-{index}") for index in range(10)),
            ),
            TreeNode(value="readme.md", path="readme.md"),
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


def test_filter_keeps_indexes_from_the_complete_tree() -> None:
    tree = SourceTree(
        roots=(
            TreeNode(
                value="docs",
                path="docs",
                children=(TreeNode(value="api.md", path="docs/api.md"),),
            ),
            TreeNode(value="readme.md", path="readme.md"),
        ),
        normalize_path=lambda value: "" if value == "." else value,
    )

    selected = tree.select("docs")

    assert [(node.index, node.value) for node in selected] == [("1", "docs"), ("1.1", "api.md")]
