# apiscope/view/_lib/llmstxt/viewer.py
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view._lib.errors import ViewProjectionError
from apiscope.view._lib.tree import SourceTree, TreeNode, root_path

_H1 = re.compile(r"^\s*#\s+(?!#)(?P<title>\S.*)$")
_H2 = re.compile(r"^\s*##\s+(?!#)(?P<title>\S.*)$")
_LINK = re.compile(
    r"^\s*[-*]\s+\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)"
    r"(?:\s*:\s*(?P<description>.*))?\s*$"
)


@dataclass(slots=True)
class _Section:
    title: str
    path: str
    links: list[TreeNode] = field(default_factory=list)


class LlmstxtViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        path = _content_file(content, metadata)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            raise ViewProjectionError("view.document_invalid") from error

        sections: list[_Section] = []
        section_counts: dict[str, int] = {}
        current: _Section | None = None
        for line in lines:
            heading = _H2.match(line)
            if heading is not None:
                title = heading.group("title").strip()
                occurrence = section_counts.get(title, 0) + 1
                section_counts[title] = occurrence
                section_path = f"section/{title}" if occurrence == 1 else f"section/{title}#{occurrence}"
                current = _Section(title=title, path=section_path)
                sections.append(current)
                continue

            if current is None:
                continue
            link = _LINK.match(line)
            if link is None:
                continue
            title = link.group("title").strip()
            url = link.group("url").strip()
            description = (link.group("description") or "").strip()
            value = url if not description else f"{url} — {description}"
            current.links.append(
                TreeNode(
                    value=value,
                    kind="key_value",
                    key=title or url,
                    path=f"{current.path}/{len(current.links) + 1}",
                )
            )

        has_overview = any(_H1.match(line) is not None for line in lines) or bool(lines)
        roots: list[TreeNode] = []
        if has_overview:
            roots.append(TreeNode(value="Overview", path="overview"))
        roots.extend(
            TreeNode(value=section.title, children=tuple(section.links), path=section.path) for section in sections
        )
        return SourceTree(roots=tuple(roots), normalize_path=_normalize_llmstxt_path)


def _content_file(content: Path, metadata: CacheMetadata) -> Path:
    if metadata.content_kind != "file" or metadata.content_name is None:
        raise ViewProjectionError("view.document_invalid")
    path = content / metadata.content_name
    if path.parent != content or not path.is_file():
        raise ViewProjectionError("view.content_invalid")
    return path


def _normalize_llmstxt_path(value: str) -> str:
    normalized = root_path(value)
    if not normalized:
        return ""
    if normalized == "overview" or normalized.startswith("section/"):
        return normalized
    raise ViewProjectionError("view.path_invalid", {"path": value})
