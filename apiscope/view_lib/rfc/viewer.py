# apiscope/view_lib/rfc/viewer.py
from __future__ import annotations

from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.rfc.text import split_pages
from apiscope.view_lib.rfc.xml import RfcNode, RfcXmlError, parse_rfc_xml
from apiscope.view_lib.schema import TreeNode
from apiscope.view_lib.tree import SourceTree, root_path


class RfcViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        path = _content_file(content, metadata)
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error

        if _looks_like_xml(raw, path):
            try:
                nodes = parse_rfc_xml(raw)
            except RfcXmlError as error:
                raise ProjectionError(ProjectionReason.DOCUMENT_INVALID) from error
            roots = [_to_tree_node(node) for node in nodes]
        else:
            text = raw.decode("utf-8", errors="replace")
            roots = _build_text_tree(text)
        return SourceTree(roots=tuple(roots), normalize_path=_normalize_rfc_path)


def _to_tree_node(node: RfcNode) -> TreeNode:
    children = tuple(_to_tree_node(child) for child in node.children)
    return TreeNode(
        key=node.key,
        description=node.description,
        children=children,
        path=node.route,
    )


def _build_text_tree(text: str) -> list[TreeNode]:
    pages = split_pages(text)
    if not pages:
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID)
    children = tuple(TreeNode(key=str(number), path=f"page/{number}") for number, _ in enumerate(pages, start=1))
    return [TreeNode(key="page", children=children, path="page", node_type="ordinary")]


def _looks_like_xml(raw: bytes, path: Path) -> bool:
    return path.suffix.lower() in {".xml", ".rfcxml"} or raw.lstrip().startswith(b"<rfc")


def _content_file(content: Path, metadata: CacheMetadata) -> Path:
    if metadata.content_kind != "file" or metadata.content_name is None:
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID)
    path = content / metadata.content_name
    if path.parent != content or not path.is_file():
        raise ProjectionError(ProjectionReason.CONTENT_INVALID)
    return path


def _normalize_rfc_path(value: str) -> str:
    return root_path(value)
