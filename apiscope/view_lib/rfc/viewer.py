# apiscope/view_lib/rfc/viewer.py
from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.tree import SourceTree, TreeNode, root_path

_NUMBERED_HEADING = re.compile(r"^(?P<number>\d+(?:\.\d+)*)\.\s+(?P<title>.+?)\s*$")
_APPENDIX_HEADING = re.compile(r"^(?P<number>Appendix\s+[A-Z])\.?\s+(?P<title>.+?)\s*$", re.IGNORECASE)
_CITATION = re.compile(r"^\s*\[(?P<key>[^\]]+)\]\s+(?P<value>\S.*)$")
_REFERENCE_HEADINGS = {"normative references", "informative references", "references"}
_UNNUMBERED_HEADINGS = {
    "acknowledgements",
    "acknowledgments",
    "authors' addresses",
    "copyright notice",
    "iana considerations",
    "security considerations",
    "status of this memo",
}


@dataclass(slots=True)
class _Section:
    label: str
    path: str
    depth: int
    children: list[_Section] = field(default_factory=list)


class RfcViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        path = _content_file(content, metadata)
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise ProjectionError(ProjectionReason.CONTENT_INVALID) from error

        if _looks_like_xml(raw, path):
            roots = _build_xml_tree(raw)
        else:
            try:
                text = raw.decode("utf-8", errors="replace")
            except UnicodeError as error:
                raise ProjectionError(ProjectionReason.DOCUMENT_INVALID) from error
            roots = _build_text_tree(text)
        return SourceTree(roots=tuple(roots), normalize_path=_normalize_rfc_path)


def _build_xml_tree(raw: bytes) -> list[TreeNode]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise ProjectionError(ProjectionReason.DOCUMENT_INVALID) from error

    roots: list[TreeNode] = [TreeNode(value="Overview", path="overview")]
    middle = _child(root, "middle")
    if middle is not None:
        for ordinal, section in enumerate(_children(middle, "section"), start=1):
            roots.append(_xml_section(section, fallback=f"section/{ordinal}"))

    back = _child(root, "back")
    if back is not None:
        for ordinal, references in enumerate(_children(back, "references"), start=1):
            roots.append(_xml_references(references, fallback=f"references/{ordinal}"))
    return roots


def _xml_section(element: ElementTree.Element, *, fallback: str) -> TreeNode:
    title = _element_text(_child(element, "name")) or _element_text(_child(element, "title")) or "Section"
    path = element.attrib.get("anchor") or _section_path(title, fallback)
    children = tuple(
        _xml_section(section, fallback=f"{path}/{ordinal}")
        for ordinal, section in enumerate(_children(element, "section"), start=1)
    )
    return TreeNode(value=title, children=children, path=f"section/{path}")


def _xml_references(element: ElementTree.Element, *, fallback: str) -> TreeNode:
    title = element.attrib.get("title") or "References"
    children: list[TreeNode] = []
    for ordinal, reference in enumerate(_children(element, "reference"), start=1):
        key = reference.attrib.get("anchor") or reference.attrib.get("target") or str(ordinal)
        front = _child(reference, "front")
        value = _element_text(_child(front, "title")) if front is not None else "Reference"
        children.append(
            TreeNode(
                value=value or "Reference",
                kind="key_value",
                key=key,
                path=f"references/{title}/{key}",
            )
        )
    return TreeNode(value=title, children=tuple(children), path=f"references/{title}" or fallback)


def _build_text_tree(text: str) -> list[TreeNode]:
    lines = text.splitlines()
    headings: list[tuple[int, str, int, int]] = []
    for line_number, line in enumerate(lines):
        parsed = _parse_heading(line)
        if parsed is None:
            continue
        label, depth = parsed
        headings.append((line_number, label, depth, len(headings)))

    roots: list[TreeNode] = [TreeNode(value="Overview", path="overview")]
    sections: list[_Section] = []
    stack: list[_Section] = []
    reference_headings: list[tuple[int, str, int]] = []
    for line_number, label, depth, ordinal in headings:
        lowered = label.rstrip(".").strip().lower()
        if lowered in _REFERENCE_HEADINGS:
            reference_headings.append((line_number, label, ordinal))
            continue
        if lowered in {"abstract", "status of this memo"}:
            continue
        section = _Section(label=label, path=_section_path(label, f"unnumbered-{ordinal}"), depth=depth)
        while stack and stack[-1].depth >= depth:
            stack.pop()
        if stack:
            stack[-1].children.append(section)
        else:
            sections.append(section)
        stack.append(section)

    roots.extend(_section_to_tree(section) for section in sections)
    for index, (line_number, label, _) in enumerate(reference_headings):
        end = reference_headings[index + 1][0] if index + 1 < len(reference_headings) else len(lines)
        citations = tuple(_text_citations(lines[line_number + 1 : end], label))
        roots.append(TreeNode(value=label, children=citations, path=f"references/{label}"))
    return roots


def _section_to_tree(section: _Section) -> TreeNode:
    return TreeNode(
        value=section.label,
        children=tuple(_section_to_tree(child) for child in section.children),
        path=f"section/{section.path}",
    )


def _text_citations(lines: list[str], group: str) -> list[TreeNode]:
    citations: list[TreeNode] = []
    for line in lines:
        match = _CITATION.match(line)
        if match is None:
            continue
        key = match.group("key").strip()
        citations.append(
            TreeNode(
                value=match.group("value").strip(),
                kind="key_value",
                key=key,
                path=f"references/{group}/{key}",
            )
        )
    return citations


def _parse_heading(line: str) -> tuple[str, int] | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 160:
        return None
    if re.search(r"\.{3,}\s*\d*\s*$", stripped):
        return None

    match = _NUMBERED_HEADING.match(stripped)
    if match is not None:
        number = match.group("number")
        return f"{number}. {match.group('title').strip()}", number.count(".") + 1

    match = _APPENDIX_HEADING.match(stripped)
    if match is not None:
        return f"{match.group('number')}. {match.group('title').strip()}", 1

    lowered = stripped.rstrip(".").lower()
    if lowered in _REFERENCE_HEADINGS or lowered in _UNNUMBERED_HEADINGS:
        return stripped, 1
    return None


def _section_path(label: str, fallback: str) -> str:
    match = _NUMBERED_HEADING.match(label)
    if match is not None:
        return match.group("number")
    appendix = _APPENDIX_HEADING.match(label)
    if appendix is not None:
        return appendix.group("number").lower().replace(" ", "-")
    return fallback


def _child(element: ElementTree.Element | None, name: str) -> ElementTree.Element | None:
    if element is None:
        return None
    return next((child for child in element if _local_name(child.tag) == name), None)


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _element_text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


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
    normalized = root_path(value)
    if not normalized:
        return ""
    if not normalized.startswith(("overview", "section/", "references/")):
        raise ProjectionError(ProjectionReason.PATH_INVALID, {"path": value})
    return normalized
