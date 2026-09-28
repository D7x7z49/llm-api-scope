# apiscope/view_lib/tree.py
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias

from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.schema import IndexedNode, PathNormalizer, TreeNode


@dataclass(frozen=True, slots=True)
class SourceTree:
    roots: tuple[TreeNode, ...]
    normalize_path: PathNormalizer

    def __post_init__(self) -> None:
        _validate_unique_keys(self.roots)

    def indexed(self) -> tuple[IndexedNode, ...]:
        return tuple(_flatten(_index_nodes(self.roots, prefix=(), parent_index="")))

    def resolve(self, path: str) -> IndexedNode:
        normalized = self.normalize_path(path)
        if not normalized:
            raise ProjectionError(ProjectionReason.PATH_NOT_FOUND, self._missing_path_values(path, normalized))
        return self._resolve_normalized(path, normalized, self.indexed())

    def select(self, path: str | None, *, depth: int | None = None) -> tuple[IndexedNode, ...]:
        indexed = self.indexed()
        if path is None:
            return _within_depth(indexed, (), depth)

        normalized = self.normalize_path(path)
        if not normalized:
            return _within_depth(indexed, (), depth)

        selected = self._resolve_normalized(path, normalized, indexed)
        scoped = tuple(node for node in indexed if _is_descendant_or_self(node.address, selected.address))
        return _reindex_members(_within_depth(scoped, selected.address, depth), selected.address)

    def children_of(
        self,
        node: IndexedNode | None,
        nodes: tuple[IndexedNode, ...] | None = None,
    ) -> tuple[IndexedNode, ...]:
        parent_address = () if node is None else node.address
        source = self.indexed() if nodes is None else nodes
        return tuple(
            candidate
            for candidate in source
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
        return matches[0]

    def _missing_path_values(
        self,
        path: str,
        normalized: str,
        indexed: tuple[IndexedNode, ...] | None = None,
    ) -> dict[str, object]:
        nodes = self.indexed() if indexed is None else indexed
        prefixes = [node for node in nodes if node.path and _is_route_prefix(node.path, normalized)]
        prefix_node = max(prefixes, key=lambda node: len(node.path or ""), default=None)
        children = self.children_of(prefix_node, nodes)
        return {
            "path": path,
            "prefix": "." if prefix_node is None else prefix_node.path or prefix_node.key,
            "nodes": hint_nodes(children),
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
            key=node.key,
            node_type=node.node_type or ("ordinary" if node.children else "leaf"),
            description=node.description,
            path=node.path,
            source_target=node.source_target,
        )
        indexed.append((current, _index_nodes(node.children, prefix=address, parent_index=index)))
    return tuple(indexed)


def _flatten(nodes: tuple[IndexedBranch, ...]) -> list[IndexedNode]:
    flattened: list[IndexedNode] = []
    for node, children in nodes:
        flattened.append(node)
        flattened.extend(_flatten(children))
    return flattened


def _reindex_members(nodes: tuple[IndexedNode, ...], scope_address: tuple[int, ...]) -> tuple[IndexedNode, ...]:
    if not nodes:
        return ()

    scope_depth = len(scope_address)
    counts: dict[tuple[int, ...], int] = {}
    for node in nodes:
        depth = len(node.address) - scope_depth
        if depth <= 0:
            continue
        parent = node.address[: scope_depth + depth - 1]
        counts[parent] = counts.get(parent, 0) + 1

    indexes: dict[tuple[int, ...], str] = {}
    result: list[IndexedNode] = []
    for node in nodes:
        depth = len(node.address) - scope_depth
        if depth <= 0:
            continue
        parent = node.address[: scope_depth + depth - 1]
        width = len(str(counts[parent]))
        segment = str(node.address[scope_depth + depth - 1]).zfill(width)
        index = segment if depth == 1 else f"{indexes[parent]}.{segment}"
        indexes[node.address] = index
        result.append(
            IndexedNode(
                address=node.address,
                index=index,
                key=node.key,
                node_type=node.node_type,
                description=node.description,
                path=node.path,
                source_target=node.source_target,
            )
        )
    return tuple(result)


def _within_depth(
    nodes: Iterable[IndexedNode],
    anchor_address: tuple[int, ...],
    depth: int | None,
) -> tuple[IndexedNode, ...]:
    if depth is None:
        return tuple(nodes)
    limit = len(anchor_address) + depth
    return tuple(node for node in nodes if len(node.address) <= limit)


def hint_nodes(children: Iterable[IndexedNode]) -> list[dict[str, object]]:
    child_list = tuple(children)
    width = len(str(len(child_list))) if child_list else 1
    items: list[dict[str, object]] = []
    for ordinal, node in enumerate(child_list, start=1):
        item: dict[str, object] = {
            "index": str(ordinal).zfill(width),
            "key": node.key,
            "node_type": node.node_type,
        }
        if node.description is not None:
            item["description"] = node.description
        items.append(item)
    return items


def _validate_unique_keys(nodes: Iterable[TreeNode]) -> None:
    seen: set[str] = set()
    for node in nodes:
        if node.key in seen:
            raise ProjectionError(ProjectionReason.DUPLICATE_KEY, {"key": node.key})
        seen.add(node.key)
        _validate_unique_keys(node.children)


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
