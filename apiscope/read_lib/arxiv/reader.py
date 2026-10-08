# apiscope/read_lib/arxiv/reader.py
from __future__ import annotations

from pathlib import Path

from apiscope.cache import CacheMetadata, resolve_content_file
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.arxiv.html import ArxivHtmlError, ArxivSection, parse_arxiv_html
from apiscope.view_lib.schema import IndexedNode


class ArxivReader:
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
    ) -> ReadResult:
        if not target.is_leaf or target.path is None:
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path or target.index})
        if metadata.content_kind != "file" or metadata.content_name is None:
            return FilesystemReader().read(content, metadata, target)
        if Path(metadata.content_name).suffix.lower() != ".html":
            return FilesystemReader().read(content, metadata, target)
        path = resolve_content_file(content, metadata)
        if path is None:
            raise ReadError(ReadReason.CONTENT_INVALID)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ReadError(ReadReason.CONTENT_INVALID) from error
        try:
            section = _find_section(parse_arxiv_html(source), target.path)
        except ArxivHtmlError as error:
            raise ReadError(ReadReason.CONTENT_INVALID) from error
        if section is None or section.end is None:
            raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})
        selected = source[section.start : section.end]
        return ReadResult(
            target=target.path,
            kind="text",
            content=selected,
            media_type="text/html",
            encoding="utf-8",
            size=len(selected.encode("utf-8")),
        )


def _find_section(sections: tuple[ArxivSection, ...], target: str) -> ArxivSection | None:
    for section in sections:
        if section.route == target:
            return section
        found = _find_section(tuple(section.children), target)
        if found is not None:
            return found
    return None
