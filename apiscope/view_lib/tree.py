# apiscope/view_lib/tree.py
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal, TypeAlias

from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError

NodeKind = Literal["value", "key_value"]
PathNormalizer = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class TreeNode:
    value: str
    kind: NodeKind = "value"
    key: str | None = None
    children: tuple[TreeNode, ...] = ()
    path: str | None = None

    def __post_init__(self) -> None:
        if self.kind == "key_value" and self.key is None:
            raise ValueError("key-value nodes require a key")
        if self.kind == "value" and self.key is not None:
            raise ValueError("value nodes cannot have a key")
        if not self.value.strip():
            raise ValueError("tree node values must not be empty")


@dataclass(frozen=True, slots=True)
class IndexedNode:
    address: tuple[int, ...]
    index: str
    value: str
    kind: NodeKind
    key: str | None = None
    path: str | None = None

    def as_data(self) -> dict[str, str]:
        data = {
            "index": self.index,
            "kind": self.kind,
            "value": self.value,
        }
        if self.key is not None:
            data["key"] = self.key
        return data


@dataclass(frozen=True, slots=True)
class SourceTree:
    roots: tuple[TreeNode, ...]
    normalize_path: PathNormalizer

    def indexed(self) -> tuple[IndexedNode, ...]:
        return tuple(_flatten(_index_nodes(self.roots, prefix=(), parent_index="")))

    def select(self, path: str | None) -> tuple[IndexedNode, ...]:
        indexed = self.indexed()
        if path is None:
            return indexed

        normalized = self.normalize_path(path)
        if not normalized:
            return indexed

        matches = [node for node in indexed if node.path == normalized]
        if not matches:
            raise ProjectionError(ProjectionReason.PATH_NOT_FOUND, {"path": path})
        if len(matches) > 1:
            raise ProjectionError(ProjectionReason.PATH_AMBIGUOUS, {"path": path})

        selected = matches[0]
        return tuple(node for node in indexed if _is_descendant_or_self(node.address, selected.address))


IndexedBranch: TypeAlias = tuple[IndexedNode, tuple["IndexedBranch", ...]]


def _index_nodes(
    nodes: Iterable[TreeNode],
    *,
    prefix: tuple[int, ...],
    parent_index: str,
) -> tuple[IndexedBranch, ...]:
    node_list = tuple(nodes)
    if not node_list:
        return ()

    width = len(str(len(node_list)))
    indexed: list[IndexedBranch] = []
    for ordinal, node in enumerate(node_list, start=1):
        address = (*prefix, ordinal)
        segment = str(ordinal).zfill(width)
        index = segment if not parent_index else f"{parent_index}.{segment}"
        current = IndexedNode(
            address=address,
            index=index,
            value=node.value,
            kind=node.kind,
            key=node.key,
            path=node.path,
        )
        indexed.append((current, _index_nodes(node.children, prefix=address, parent_index=index)))
    return tuple(indexed)


def _flatten(nodes: tuple[IndexedBranch, ...]) -> list[IndexedNode]:
    flattened: list[IndexedNode] = []
    for node, children in nodes:
        flattened.append(node)
        flattened.extend(_flatten(children))
    return flattened


def _is_descendant_or_self(address: tuple[int, ...], ancestor: tuple[int, ...]) -> bool:
    return address[: len(ancestor)] == ancestor


def root_path(path: str) -> str:
    value = path.strip()
    if value in {"", "."}:
        return ""
    return value
