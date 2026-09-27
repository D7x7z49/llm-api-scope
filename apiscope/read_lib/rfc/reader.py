# apiscope/read_lib/rfc/reader.py
from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.rfc.text import split_pages
from apiscope.view_lib.rfc.xml import RfcNode, RfcXmlError, parse_rfc_xml
from apiscope.view_lib.schema import IndexedNode


class RfcReader:
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult:
        if not target.is_leaf or target.path is None:
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path or target.index})
        path = _content_file(content, metadata)
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise ReadError(ReadReason.READ_FAILED, {"target": target.path}) from error

        if _looks_like_xml(raw, path):
            return _read_xml(raw, target.path)

        text = raw.decode("utf-8", errors="replace")
        pages = split_pages(text)
        page_number = _page_number(target.path)
        if page_number is None:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path})
        if page_number > len(pages):
            raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})
        return _text_result(target.path, pages[page_number - 1], "text/plain")


def _read_xml(raw: bytes, target: str) -> ReadResult:
    try:
        nodes = parse_rfc_xml(raw)
    except RfcXmlError as error:
        raise ReadError(ReadReason.CONTENT_INVALID) from error
    element = _find_element(nodes, target)
    if element is None:
        raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target})
    text = ElementTree.tostring(element, encoding="unicode")
    return _text_result(target, text, "application/rfc+xml")


def _find_element(nodes: tuple[RfcNode, ...], target: str) -> ElementTree.Element | None:
    for node in nodes:
        if node.route == target:
            return node.element
        found = _find_element(node.children, target)
        if found is not None:
            return found
    return None


def _page_number(target: str) -> int | None:
    prefix, separator, value = target.partition("/")
    if prefix != "page" or not separator:
        return None
    try:
        number = int(value)
    except ValueError:
        return None
    return number if number > 0 else None


def _text_result(target: str, text: str, media_type: str) -> ReadResult:
    size = len(text.encode("utf-8"))
    return ReadResult(
        target=target,
        kind="text",
        content=text,
        media_type=media_type,
        encoding="utf-8",
        size=size,
    )


def _looks_like_xml(raw: bytes, path: Path) -> bool:
    return path.suffix.lower() in {".xml", ".rfcxml"} or raw.lstrip().startswith(b"<rfc")


def _content_file(content: Path, metadata: CacheMetadata) -> Path:
    if metadata.content_kind != "file" or metadata.content_name is None:
        raise ReadError(ReadReason.CONTENT_INVALID)
    try:
        root = content.resolve(strict=True)
        path = (root / metadata.content_name).resolve(strict=True)
        path.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        raise ReadError(ReadReason.CONTENT_INVALID) from error
    if not path.is_file():
        raise ReadError(ReadReason.CONTENT_INVALID)
    return path
