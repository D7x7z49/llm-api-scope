# apiscope/view_lib/constants.py
from enum import StrEnum
from typing import Final


class ProjectionReason(StrEnum):
    CONTENT_INVALID = "view_lib.projection.content_invalid"
    PATH_INVALID = "view_lib.projection.path_invalid"
    PATH_NOT_FOUND = "view_lib.projection.path_not_found"
    DUPLICATE_KEY = "view_lib.projection.duplicate_key"
    INDEX_NOT_FOUND = "view_lib.projection.index_not_found"


class NodeLabel(StrEnum):
    OVERVIEW = "view_lib.node.overview"


class TreeInvariant(StrEnum):
    NODE_KEY_REQUIRED = "view_lib.tree.node_key_required"
    LEAF_CHILDREN_FORBIDDEN = "view_lib.tree.leaf_children_forbidden"


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    ProjectionReason.CONTENT_INVALID: "cached content is invalid",
    ProjectionReason.PATH_INVALID: "cannot view path {path} because the path is invalid",
    ProjectionReason.PATH_NOT_FOUND: "route {path} does not exist",
    ProjectionReason.DUPLICATE_KEY: "route key {key} appears more than once under the same parent",
    ProjectionReason.INDEX_NOT_FOUND: "tree index {index} does not exist",
}

OUTPUT_TEMPLATES: Final[dict[str, str]] = {
    NodeLabel.OVERVIEW: "Overview",
}

TREE_INVARIANT_MESSAGES: Final[dict[str, str]] = {
    TreeInvariant.NODE_KEY_REQUIRED: "tree node keys must not be empty",
    TreeInvariant.LEAF_CHILDREN_FORBIDDEN: "leaf nodes cannot have children",
}

__all__ = [
    "MESSAGE_TEMPLATES",
    "OUTPUT_TEMPLATES",
    "TREE_INVARIANT_MESSAGES",
    "NodeLabel",
    "ProjectionReason",
    "TreeInvariant",
]
