# apiscope/view_lib/filesystem/viewer.py
from __future__ import annotations

import posixpath
import unicodedata
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.tree import SourceTree, TreeNode, root_path


class FilesystemViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        return build_filesystem_tree(content, metadata, exclude_git=False)


def build_filesystem_tree(
    content: Path,
    metadata: CacheMetadata,
    *,
    exclude_git: bool,
) -> SourceTree:
    if metadata.content_kind == "file":
        if metadata.content_name is None:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)
        file_path = content / metadata.content_name
        if file_path.parent != content or not file_path.is_file():
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)
        roots: tuple[TreeNode, ...] = (TreeNode(value=file_path.name, path=file_path.name),)
    else:
        if not content.is_dir():
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)
        roots = tuple(_directory_nodes(content, exclude_git=exclude_git))
    return SourceTree(roots=roots, normalize_path=_normalize_filesystem_path)


def _directory_nodes(directory: Path, *, exclude_git: bool, prefix: str = "") -> list[TreeNode]:
    children = [child for child in directory.iterdir() if not (exclude_git and child.name == ".git")]
    children.sort(key=lambda child: _sort_key(_relative_path(child, prefix)))

    nodes: list[TreeNode] = []
    for child in children:
        relative = _relative_path(child, prefix)
        if child.is_dir():
            nodes.append(
                TreeNode(
                    value=child.name,
                    path=relative,
                    children=tuple(_directory_nodes(child, exclude_git=exclude_git, prefix=relative)),
                    node_type="ordinary",
                )
            )
        else:
            nodes.append(TreeNode(value=child.name, path=relative))
    return nodes


def _relative_path(path: Path, prefix: str) -> str:
    return f"{prefix}/{path.name}" if prefix else path.name


def _sort_key(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def _normalize_filesystem_path(value: str) -> str:
    normalized = root_path(value).replace("\\", "/")
    if not normalized:
        return ""
    normalized = posixpath.normpath(normalized)
    if normalized == "." or normalized.startswith("../") or normalized == ".." or normalized.startswith("/"):
        raise ProjectionError(ProjectionReason.PATH_INVALID, {"path": value})
    return normalized
