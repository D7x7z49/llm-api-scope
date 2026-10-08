# apiscope/view_lib/arxiv/html.py
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser


class ArxivHtmlError(ValueError):
    pass


@dataclass(slots=True)
class ArxivSection:
    route: str
    title: str | None
    start: int
    end: int | None = None
    children: list[ArxivSection] = field(default_factory=list)


@dataclass(slots=True)
class _SectionTag:
    section: ArxivSection | None


class _SectionParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__()
        self.source = source
        self.line_offsets = [0]
        for line in source.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))
        self.roots: list[ArxivSection] = []
        self.section_tags: list[_SectionTag] = []
        self.heading_tag: str | None = None
        self.heading_parts: list[str] = []
        self.heading_section: ArxivSection | None = None
        self.routes: set[str] = set()
        self.section_number = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "section":
            section = self._new_section(attributes) if _is_section(attributes.get("class")) else None
            self.section_tags.append(_SectionTag(section))
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            if _has_class(attributes.get("class"), "ltx_title"):
                self.heading_tag = tag
                self.heading_parts = []
                self.heading_section = self._current_section()

    def handle_endtag(self, tag: str) -> None:
        if tag == self.heading_tag and self.heading_tag is not None:
            title = " ".join("".join(self.heading_parts).split())
            if self.heading_section is not None and title:
                self.heading_section.title = title
            self.heading_tag = None
            self.heading_section = None
            self.heading_parts = []
        if tag == "section" and self.section_tags:
            tagged = self.section_tags.pop()
            if tagged.section is not None:
                tagged.section.end = self._position_after_tag()

    def handle_data(self, data: str) -> None:
        if self.heading_tag is not None:
            self.heading_parts.append(data)

    def _new_section(self, attrs: dict[str, str | None]) -> ArxivSection:
        self.section_number += 1
        base_route = attrs.get("id") or f"section-{self.section_number}"
        route = base_route
        suffix = 1
        while route in self.routes:
            route = f"{base_route}-{suffix}"
            suffix += 1
        self.routes.add(route)
        section = ArxivSection(route=route, title=None, start=self._position())
        parent = self._current_section()
        if parent is None:
            self.roots.append(section)
        else:
            parent.children.append(section)
        return section

    def _current_section(self) -> ArxivSection | None:
        return next(
            (tagged.section for tagged in reversed(self.section_tags) if tagged.section is not None),
            None,
        )

    def _position(self) -> int:
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def _position_after_tag(self) -> int:
        end = self.source.find(">", self._position())
        if end < 0:
            raise ArxivHtmlError("section closing tag is incomplete")
        return end + 1


def parse_arxiv_html(source: str) -> tuple[ArxivSection, ...]:
    parser = _SectionParser(source)
    try:
        parser.feed(source)
        parser.close()
    except (AssertionError, ValueError) as error:
        raise ArxivHtmlError("paper html cannot be parsed") from error
    if parser.section_tags or not parser.roots:
        raise ArxivHtmlError("paper html has no complete section tree")
    if any(not _is_complete(section) for section in parser.roots):
        raise ArxivHtmlError("paper html has an incomplete section")
    return tuple(parser.roots)


def _is_complete(section: ArxivSection) -> bool:
    return section.end is not None and all(_is_complete(child) for child in section.children)


def _is_section(value: str | None) -> bool:
    classes = set((value or "").split())
    return bool(
        classes
        & {
            "ltx_section",
            "ltx_subsection",
            "ltx_subsubsection",
            "ltx_paragraph",
            "ltx_subparagraph",
        }
    )


def _has_class(value: str | None, name: str) -> bool:
    return name in (value or "").split()
