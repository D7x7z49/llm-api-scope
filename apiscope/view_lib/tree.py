# apiscope/view_lib/tree.py
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal, TypeAlias

from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError

NodeKind = Literal["value", "key_value"]
NodeType = Literal["ordinary", "leaf"]
PathNormalizer = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class TreeNode:
    value: str
    kind: NodeKind = "value"
    key: str | None = None
    children: tuple[TreeNode, ...] = ()
    path: str | None = None
    node_type: NodeType | None = None

    def __post_init__(self) -> None:
        if self.kind == "key_value" and self.key is None:
            raise ValueError("key-value nodes require a key")
        if self.kind == "value" and self.key is not None:
            raise ValueError("value nodes cannot have a key")
        if not self.value.strip():
            raise ValueError("tree node values must not be empty")
        if self.node_type is None:
            object.__setattr__(self, "node_type", "ordinary" if self.children else "leaf")
        elif self.node_type == "leaf" and self.children:
            raise ValueError("leaf nodes cannot have children")


@dataclass(frozen=True, slots=True)
class IndexedNode:
    address: tuple[int, ...]
    index: str
    value: str
    kind: NodeKind
    node_type: NodeType
    key: str | None = None
    path: str | None = None

    @property
    def is_leaf(self) -> bool:
        return self.node_type == "leaf"

    def as_data(self) -> dict[str, str]:
        data = {
            "index": self.index,
            "kind": self.kind,
            "node_type": self.node_type,
            "value": self.value,
        }
        if self.key is not None:
            data["key"] = self.key
        if self.path is not None:
            data["path"] = self.path
        return data


@dataclass(frozen=True, slots=True)
class SourceTree:
    roots: tuple[TreeNode, ...]
    normalize_path: PathNormalizer

    def indexed(self) -> tuple[IndexedNode, ...]:
        return tuple(_flatten(_index_nodes(self.roots, prefix=(), parent_index="")))

    def resolve(self, path: str) -> IndexedNode:
        normalized = self.normalize_path(path)
        if not normalized:
            raise ProjectionError(ProjectionReason.PATH_NOT_FOUND, self._missing_path_values(path, normalized))
        return self._resolve_normalized(path, normalized, self.indexed())

    def resolve_index(self, index: str) -> IndexedNode:
        for node in self.indexed():
            if node.index == index:
                return node
        raise ProjectionError(ProjectionReason.INDEX_NOT_FOUND, {"index": index})

    def select(self, path: str | None) -> tuple[IndexedNode, ...]:
        indexed = self.indexed()
        if path is None:
            return indexed

        normalized = self.normalize_path(path)
        if not normalized:
            return indexed

        selected = self._resolve_normalized(path, normalized, indexed)
        return tuple(node for node in indexed if _is_descendant_or_self(node.address, selected.address))

    def children_of(self, node: IndexedNode | None) -> tuple[IndexedNode, ...]:
        parent_address = () if node is None else node.address
        return tuple(
            candidate
            for candidate in self.indexed()
            if len(candidate.address) == len(parent_address) + 1
            and _is_descendant_or_self(candidate.address, parent_address)
        )

    def _resolve_normalized(
        self,
        path: str,
        normalized: str,
        indexed: tuple[IndexedNode, ...],
    ) -> IndexedNode:
        matches = [node for node in indexed if node.path == normalized]
        if not matches:
            raise ProjectionError(ProjectionReason.PATH_NOT_FOUND, self._missing_path_values(path, normalized, indexed))
        if len(matches) > 1:
            raise ProjectionError(ProjectionReason.PATH_AMBIGUOUS, self._ambiguous_path_values(path, matches, indexed))
        return matches[0]

    def _ambiguous_path_values(
        self,
        path: str,
        matches: list[IndexedNode],
        indexed: tuple[IndexedNode, ...],
    ) -> dict[str, object]:
        parent_address = matches[0].address[:-1]
        while parent_address and any(node.address[: len(parent_address)] != parent_address for node in matches[1:]):
            parent_address = parent_address[:-1]
        parent = next((node for node in indexed if node.address == parent_address), None)
        routes = [
            {
                "index": node.index,
                "route": node.path or node.value,
                "label": node.key or node.value,
                "node_type": node.node_type,
            }
            for node in matches
        ]
        routes_text = ", ".join(f"{item['route']} [{item['index']}]" for item in routes)
        return {
            "path": path,
            "prefix": "." if parent is None else parent.path or parent.value,
            "routes": routes,
            "routes_text": routes_text,
        }

    def _missing_path_values(
        self,
        path: str,
        normalized: str,
        indexed: tuple[IndexedNode, ...] | None = None,
    ) -> dict[str, object]:
        nodes = self.indexed() if indexed is None else indexed
        prefixes = [node for node in nodes if node.path and _is_route_prefix(node.path, normalized)]
        prefix_node = max(prefixes, key=lambda node: len(node.path or ""), default=None)
        children = self.children_of(prefix_node)
        routes = [
            {
                "index": node.index,
                "route": node.path or node.value,
                "label": node.key or node.value,
            }
            for node in children
        ]
        routes_text = ", ".join(f"{item['route']} [{item['index']}]" for item in routes) or "(none)"
        return {
            "path": path,
            "prefix": "." if prefix_node is None else prefix_node.path or prefix_node.value,
            "routes": routes,
            "routes_text": routes_text,
        }


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
            node_type=node.node_type or ("ordinary" if node.children else "leaf"),
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


def _is_route_prefix(prefix: str, route: str) -> bool:
    if prefix == route:
        return False
    if prefix == "/":
        return route.startswith("/")
    return route.startswith(f"{prefix.rstrip('/')}/")


def root_path(path: str) -> str:
    value = path.strip()
    if value in {"", "."}:
        return ""
    return value
