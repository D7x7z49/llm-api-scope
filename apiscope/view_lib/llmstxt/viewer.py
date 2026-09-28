# apiscope/view_lib/llmstxt/viewer.py
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from apiscope.cache import CacheMetadata, resolve_content_file
from apiscope.view_lib.constants import OUTPUT_TEMPLATES, NodeLabel, ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.schema import TreeNode
from apiscope.view_lib.tree import SourceTree, root_path

_LINK = re.compile(
    r"^\s*[-*]\s+\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)"
    r"(?:\s*:\s*(?P<description>.*))?\s*$"
)


@dataclass(slots=True)
class _Link:
    target: str
    description: str


@dataclass(slots=True)
class _Directory:
    children: dict[str, _Directory] = field(default_factory=dict)
    link: _Link | None = None


class LlmstxtViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        path = resolve_content_file(content, metadata)
        if path is None:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error

        links: dict[str, _Link] = {}
        for line in lines:
            match = _LINK.match(line)
            if match is None:
                continue
            title = match.group("title").strip()
            target = _resolve_target(metadata.source, match.group("url").strip())
            route = _route_path(metadata.source, target)
            note = (match.group("description") or "").strip()
            links.setdefault(
                route,
                _Link(target=target, description=_link_description(title or target, note)),
            )

        roots: list[TreeNode] = []
        if lines:
            roots.append(TreeNode(key=OUTPUT_TEMPLATES[NodeLabel.OVERVIEW], path="overview"))
        roots.extend(_route_nodes(_build_directories(links)))
        return SourceTree(roots=tuple(roots), normalize_path=_normalize_llmstxt_path)


def _link_description(title: str, note: str) -> str:
    label = f"[{title}]"
    return f"{label} {note}" if note else label


def _build_directories(links: dict[str, _Link]) -> _Directory:
    root = _Directory()
    for route, link in links.items():
        current = root
        for segment in route.split("/"):
            current = current.children.setdefault(segment, _Directory())
        current.link = link
    return root


def _route_nodes(directory: _Directory, prefix: str = "") -> list[TreeNode]:
    nodes: list[TreeNode] = []
    for segment in sorted(directory.children):
        child = directory.children[segment]
        route = f"{prefix}/{segment}" if prefix else segment
        if child.children:
            nodes.append(
                TreeNode(
                    key=segment,
                    children=tuple(_route_nodes(child, route)),
                    path=route,
                    node_type="ordinary",
                )
            )
        elif child.link is not None:
            nodes.append(
                TreeNode(
                    key=segment,
                    description=child.link.description,
                    path=route,
                    source_target=child.link.target,
                )
            )
    return nodes


def _resolve_target(source: str, link: str) -> str:
    try:
        target = urljoin(source, link)
        parts = urlsplit(target)
    except ValueError as error:
        raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error
    if parts.username is not None or parts.password is not None:
        raise ProjectionError(ProjectionReason.CONTENT_INVALID)
    return target


def _route_path(source: str, target: str) -> str:
    try:
        source_parts = urlsplit(source)
        target_parts = urlsplit(target)
    except ValueError as error:
        raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error
    path = target_parts.path
    same_origin = (
        source_parts.scheme.lower() == target_parts.scheme.lower()
        and source_parts.netloc.lower() == target_parts.netloc.lower()
        and bool(target_parts.netloc)
    )

    if target_parts.netloc and not same_origin:
        path = f"{target_parts.netloc}/{path.lstrip('/')}"
    else:
        base = source_parts.path.rpartition("/")[0].rstrip("/")
        if base and (path == base or path.startswith(f"{base}/")):
            path = path[len(base) :]

    route = path.strip("/")
    return route or "index"


def _normalize_llmstxt_path(value: str) -> str:
    normalized = root_path(value).strip("/")
    if not normalized:
        return ""
    return normalized
