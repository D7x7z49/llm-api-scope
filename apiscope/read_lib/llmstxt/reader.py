# apiscope/read_lib/llmstxt/reader.py
from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from apiscope.cache import CacheMetadata, resolve_content_file
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.schema import ReadKind, ReadResult
from apiscope.view_lib.schema import IndexedNode

HTTP_TIMEOUT_SECONDS = 30.0
_MARKDOWN_MEDIA_TYPES = {"text/markdown", "text/x-markdown"}


class LlmstxtReader:
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
        if target.path == "overview":
            return _read_index(content, metadata, target.path)

        url = target.source_target
        if url is None:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path})
        try:
            parts = urlsplit(url)
        except ValueError as error:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path}) from error
        if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path})
        if parts.username is not None or parts.password is not None:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path})

        try:
            if proxy is None:
                client = httpx.Client(
                    follow_redirects=True,
                    timeout=HTTP_TIMEOUT_SECONDS,
                    trust_env=False,
                    headers={"Accept": "text/markdown, text/plain;q=0.9, */*;q=0.1"},
                )
            else:
                client = httpx.Client(
                    follow_redirects=True,
                    timeout=HTTP_TIMEOUT_SECONDS,
                    proxy=proxy,
                    trust_env=False,
                    headers={"Accept": "text/markdown, text/plain;q=0.9, */*;q=0.1"},
                )
            with client:
                response = client.get(url)
                response.raise_for_status()
                raw = response.content
                content_type = response.headers.get("content-type", "")
                response_encoding = response.encoding
        except (httpx.HTTPError, httpx.InvalidURL, OSError, ValueError) as error:
            raise ReadError(ReadReason.READ_FAILED, {"target": target.path}) from error

        return _response_result(target.path, url, raw, content_type, response_encoding)


def _read_index(content: Path, metadata: CacheMetadata, target: str) -> ReadResult:
    path = resolve_content_file(content, metadata)
    if path is None:
        raise ReadError(ReadReason.CONTENT_INVALID, {"target": target})
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise ReadError(ReadReason.CONTENT_INVALID, {"target": target}) from error
    return ReadResult(
        target=target,
        kind="markdown",
        content=text,
        media_type="text/markdown",
        encoding="utf-8",
        size=len(raw),
    )


def _response_result(
    target: str,
    url: str,
    raw: bytes,
    content_type: str,
    response_encoding: str | None,
) -> ReadResult:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if not media_type:
        media_type = mimetypes.guess_type(urlsplit(url).path)[0] or "application/octet-stream"

    encoding = response_encoding or "utf-8"
    try:
        text = raw.decode(encoding)
    except (LookupError, UnicodeError):
        return ReadResult(
            target=target,
            kind="binary",
            media_type=media_type,
            size=len(raw),
            retrieval="network",
        )

    suffix = Path(urlsplit(url).path).suffix.lower()
    markdown = media_type in _MARKDOWN_MEDIA_TYPES or (
        suffix in {".md", ".markdown"} and media_type in {"text/plain", "application/octet-stream"}
    )
    kind: ReadKind = "markdown" if markdown else "text"
    return ReadResult(
        target=target,
        kind=kind,
        content=text,
        media_type=media_type,
        encoding=encoding,
        size=len(raw),
        retrieval="network",
    )
