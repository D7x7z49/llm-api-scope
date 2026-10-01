# apiscope/view_lib/schema.py
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from apiscope.view_lib.constants import TREE_INVARIANT_MESSAGES, TreeInvariant

NodeType = Literal["ordinary", "leaf"]
PathNormalizer = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class TreeNode:
    key: str
    description: str | None = None
    children: tuple[TreeNode, ...] = ()
    path: str | None = None
    node_type: NodeType | None = None
    source_target: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError(TREE_INVARIANT_MESSAGES[TreeInvariant.NODE_KEY_REQUIRED])
        if self.node_type is None:
            object.__setattr__(self, "node_type", "ordinary" if self.children else "leaf")
        elif self.node_type == "leaf" and self.children:
            raise ValueError(TREE_INVARIANT_MESSAGES[TreeInvariant.LEAF_CHILDREN_FORBIDDEN])


@dataclass(frozen=True, slots=True)
class IndexedNode:
    address: tuple[int, ...]
    index: str
    key: str
    node_type: NodeType
    description: str | None = None
    path: str | None = None
    source_target: str | None = None

    @property
    def is_leaf(self) -> bool:
        return self.node_type == "leaf"

    def as_data(self) -> dict[str, str]:
        data = {
            "index": self.index,
            "key": self.key,
            "node_type": self.node_type,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.path is not None:
            data["path"] = self.path
        return data
