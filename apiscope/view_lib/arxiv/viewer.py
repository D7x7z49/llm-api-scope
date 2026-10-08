# apiscope/view_lib/arxiv/viewer.py
from __future__ import annotations

from pathlib import Path

from apiscope.cache import CacheMetadata, resolve_content_file
from apiscope.view_lib.arxiv.html import ArxivHtmlError, ArxivSection, parse_arxiv_html
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.filesystem.viewer import build_filesystem_tree
from apiscope.view_lib.schema import TreeNode
from apiscope.view_lib.tree import SourceTree, root_path


class ArxivViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        if metadata.content_kind != "file" or metadata.content_name is None:
            return build_filesystem_tree(content, metadata, exclude_git=False)
        if Path(metadata.content_name).suffix.lower() != ".html":
            return build_filesystem_tree(content, metadata, exclude_git=False)
        path = resolve_content_file(content, metadata)
        if path is None:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error
        try:
            sections = parse_arxiv_html(source)
        except ArxivHtmlError as error:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error
        roots = _to_tree_nodes(sections)
        return SourceTree(roots=roots, normalize_path=root_path)


def _to_tree_nodes(sections: tuple[ArxivSection, ...]) -> tuple[TreeNode, ...]:
    nodes: list[TreeNode] = []
    keys: set[str] = set()
    for section in sections:
        base_key = section.title or section.route
        key = base_key
        suffix = 1
        while key in keys:
            key = f"{base_key} ({section.route}{f'-{suffix}' if suffix > 1 else ''})"
            suffix += 1
        keys.add(key)
        nodes.append(
            TreeNode(
                key=key,
                children=_to_tree_nodes(tuple(section.children)),
                path=section.route,
            )
        )
    return tuple(nodes)
