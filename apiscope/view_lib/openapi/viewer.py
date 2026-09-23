# apiscope/view_lib/openapi/viewer.py
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from apiscope.cache import CacheMetadata
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.openapi.constants import METHOD_ORDER
from apiscope.view_lib.tree import SourceTree, TreeNode, root_path

_METHOD_RANK = {method: rank for rank, method in enumerate(METHOD_ORDER)}


@dataclass(slots=True)
class _MutableNode:
    label: str
    path: str | None = None
    hint: str | None = None
    is_method: bool = False
    children: dict[str, _MutableNode] = field(default_factory=dict)


class OpenapiViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        document = _load_document(_content_file(content, metadata))
        paths = document.get("paths", {})
        if not isinstance(paths, Mapping):
            raise ProjectionError(ProjectionReason.DOCUMENT_INVALID)

        path_roots: dict[str, _MutableNode] = {}
        for path in sorted((key for key in paths if isinstance(key, str))):
            item = paths[path]
            path_item = item if isinstance(item, Mapping) else {}
            _add_path(path_roots, path, path_item)

        roots = [_to_tree_node(node) for node in _sort_nodes(path_roots.values())]
        webhooks = document.get("webhooks")
        if isinstance(webhooks, Mapping) and webhooks:
            webhook_root = _MutableNode("webhooks")
            for name in sorted((key for key in webhooks if isinstance(key, str))):
                item = webhooks[name]
                path_item = item if isinstance(item, Mapping) else {}
                webhook = _MutableNode(name, path=f"webhooks/{name}")
                webhook.hint = _path_hint(path_item)
                _add_operations(webhook, path_item)
                webhook_root.children[name] = webhook
            roots.append(_to_tree_node(webhook_root))

        return SourceTree(roots=tuple(roots), normalize_path=_normalize_openapi_path)


def _add_path(roots: dict[str, _MutableNode], path: str, path_item: Mapping[str, Any]) -> None:
    segments = _path_segments(path)
    if not segments:
        return

    current = roots
    full_segments: list[str] = []
    node: _MutableNode | None = None
    for segment in segments:
        full_segments.append(segment)
        node = current.setdefault(segment, _MutableNode(segment))
        current = node.children

    if node is None:
        return
    node.path = path
    node.hint = _path_hint(path_item)
    _add_operations(node, path_item)


def _add_operations(node: _MutableNode, path_item: Mapping[str, Any]) -> None:
    for method in METHOD_ORDER:
        operation = path_item.get(method)
        if not isinstance(operation, Mapping):
            continue
        label = method.upper()
        operation_node = _MutableNode(label, is_method=True)
        operation_node.hint = _operation_hint(operation, method)
        node.children[label] = operation_node


def _to_tree_node(node: _MutableNode) -> TreeNode:
    children = tuple(_to_tree_node(child) for child in _sort_nodes(node.children.values()))
    if node.hint is None:
        return TreeNode(value=node.label, children=children, path=node.path)
    return TreeNode(
        value=node.hint,
        kind="key_value",
        key=node.label,
        children=children,
        path=node.path,
    )


def _sort_nodes(nodes: Any) -> list[_MutableNode]:
    return sorted(
        nodes,
        key=lambda node: (
            0 if node.is_method else 1,
            _METHOD_RANK.get(node.label.lower(), len(METHOD_ORDER)),
            node.label,
        ),
    )


def _path_segments(path: str) -> list[str]:
    if path == "/":
        return ["/"]
    parts = [part for part in path.split("/") if part]
    if not parts:
        return []
    parts[0] = f"/{parts[0]}"
    return parts


def _path_hint(path_item: Mapping[str, Any]) -> str | None:
    for field_name in ("summary", "description"):
        value = path_item.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip().splitlines()[0]
    return None


def _operation_hint(operation: Mapping[str, Any], method: str) -> str:
    for field_name in ("summary", "operationId"):
        value = operation.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{method} operation"


def _content_file(content: Path, metadata: CacheMetadata) -> Path:
    if metadata.content_kind != "file" or metadata.content_name is None:
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID)
    path = content / metadata.content_name
    if path.parent != content or not path.is_file():
        raise ProjectionError(ProjectionReason.CONTENT_INVALID)
    return path


def _load_document(path: Path) -> Mapping[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID) from error
    if not isinstance(document, Mapping):
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID)
    return document


def _normalize_openapi_path(value: str) -> str:
    normalized = root_path(value)
    if not normalized:
        return ""
    if not normalized.startswith("/"):
        raise ProjectionError(ProjectionReason.PATH_INVALID, {"path": value})
    return normalized.rstrip("/") or "/"
