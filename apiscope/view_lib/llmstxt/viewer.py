# apiscope/view_lib/llmstxt/viewer.py
from __future__ import annotations

import posixpath
from pathlib import Path

from apiscope.cache import CacheMetadata, load_manifest
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.schema import TreeNode
from apiscope.view_lib.tree import SourceTree, root_path


class LlmstxtViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        manifest = load_manifest(content.parent)
        if manifest is None:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)

        keys = sorted(key for key in manifest if key != ".")
        sections = {key for key in keys if any(other != key and other.startswith(f"{key}/") for other in keys)}
        children: dict[str, list[str]] = {}
        for key in keys:
            children.setdefault(key.rpartition("/")[0], []).append(key)

        roots = tuple(_node(key, children, sections, manifest) for key in sorted(children.get("", [])))
        return SourceTree(roots=roots, normalize_path=_normalize_path)


def _node(
    key: str,
    children: dict[str, list[str]],
    sections: set[str],
    manifest: dict[str, str],
) -> TreeNode:
    is_section = key in sections
    return TreeNode(
        key=key.rpartition("/")[2],
        children=tuple(_node(child, children, sections, manifest) for child in sorted(children.get(key, []))),
        path=key,
        node_type="ordinary" if is_section else "leaf",
        source_target=None if is_section else manifest[key],
    )


def _normalize_path(value: str) -> str:
    normalized = root_path(value).replace("\\", "/")
    if not normalized:
        return ""
    normalized = posixpath.normpath(normalized)
    if normalized == "." or normalized.startswith("../") or normalized == ".." or normalized.startswith("/"):
        raise ProjectionError(ProjectionReason.PATH_INVALID, {"path": value})
    return normalized
