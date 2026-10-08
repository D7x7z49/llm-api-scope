# apiscope/sync/_lib/arxiv/fetcher.py
from __future__ import annotations

import gzip
import shutil
import tarfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path, PurePosixPath

import httpx2

from apiscope.cache import CACHE_CONTENT_DIRECTORY, digest_content
from apiscope.source import ArxivSource
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.schema import ContentKind, FetchResult, ParsedSource
from apiscope.sync._lib.transport import fetch_remote_bytes

_ARXIV_REPRESENTATION_URL = "https://arxiv.org/{representation}/{identifier}"
_PDF_SIGNATURE = b"%PDF-"
_POSTSCRIPT_SIGNATURE = b"%!PS"
_GZIP_SIGNATURE = b"\x1f\x8b"


class ArxivFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
        no_proxy: str | None = None,
    ) -> FetchResult:
        if not isinstance(source, ArxivSource):
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": "the source is not arxiv"})
        content_path = destination / CACHE_CONTENT_DIRECTORY
        content_path.mkdir(parents=True, exist_ok=True)

        html = _fetch_optional_html(source, proxy=proxy, no_proxy=no_proxy)
        if html is not None and _is_paper_html(html):
            content_name = "paper.html"
            (content_path / content_name).write_bytes(html)
            return _result(content_path, content_kind="file", content_name=content_name)

        payload = _fetch_eprint(source, proxy=proxy, no_proxy=no_proxy)
        expanded = _expand_payload(source, payload)
        if _is_unsupported_payload(expanded):
            raise SourceFetchError(source.original, "fetch.arxiv_no_structured_source")

        if _is_tar_archive(expanded):
            _extract_archive(source, expanded, content_path)
            return _result(content_path, content_kind="directory", content_name=None)

        content_name = "paper.tex"
        (content_path / content_name).write_bytes(expanded)
        return _result(content_path, content_kind="file", content_name=content_name)


def _fetch_optional_html(source: ArxivSource, *, proxy: str | None, no_proxy: str | None) -> bytes | None:
    url = _representation_url(source, "html")
    try:
        return fetch_remote_bytes(url, proxy=proxy, no_proxy=no_proxy)
    except httpx2.HTTPStatusError as error:
        if error.response.status_code == 404:
            return None
        raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
    except (OSError, ValueError, httpx2.HTTPError) as error:
        raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error


def _fetch_eprint(source: ArxivSource, *, proxy: str | None, no_proxy: str | None) -> bytes:
    url = _representation_url(source, "e-print")
    try:
        return fetch_remote_bytes(url, proxy=proxy, no_proxy=no_proxy)
    except httpx2.HTTPError as error:
        raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
    except (OSError, ValueError) as error:
        raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error


def _representation_url(source: ArxivSource, representation: str) -> str:
    return _ARXIV_REPRESENTATION_URL.format(representation=representation, identifier=source.original)


def _is_paper_html(raw: bytes) -> bool:
    return b"ltx_document" in raw.lower()


def _is_unsupported_payload(raw: bytes) -> bool:
    content = raw.lstrip()
    lowered = content[:32].lower()
    return content.startswith((_PDF_SIGNATURE, _POSTSCRIPT_SIGNATURE, b"\xf7")) or lowered.startswith(
        (b"<!doctype html", b"<html")
    )


def _expand_payload(source: ArxivSource, raw: bytes) -> bytes:
    if raw.startswith(_PDF_SIGNATURE):
        return raw
    if not raw.startswith(_GZIP_SIGNATURE):
        return raw
    try:
        return gzip.decompress(raw)
    except (OSError, EOFError) as error:
        raise SourceFetchError(source.original, "fetch.arxiv_source_invalid") from error


def _is_tar_archive(raw: bytes) -> bool:
    try:
        with tarfile.open(fileobj=BytesIO(raw), mode="r:*"):
            return True
    except tarfile.ReadError:
        return False


def _extract_archive(source: ArxivSource, raw: bytes, content_path: Path) -> None:
    extracted = False
    try:
        with tarfile.open(fileobj=BytesIO(raw), mode="r:*") as archive:
            for member in archive.getmembers():
                relative = _safe_archive_path(source, member.name)
                if member.isdir():
                    continue
                if not member.isfile() or not relative.parts:
                    raise SourceFetchError(source.original, "fetch.arxiv_source_invalid")
                stream = archive.extractfile(member)
                if stream is None:
                    raise SourceFetchError(source.original, "fetch.arxiv_source_invalid")
                target = content_path.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with stream, target.open("wb") as output:
                    shutil.copyfileobj(stream, output)
                extracted = True
    except (OSError, tarfile.TarError) as error:
        raise SourceFetchError(source.original, "fetch.arxiv_source_invalid") from error

    if not extracted:
        raise SourceFetchError(source.original, "fetch.arxiv_source_invalid")


def _safe_archive_path(source: ArxivSource, name: str) -> PurePosixPath:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise SourceFetchError(source.original, "fetch.arxiv_source_invalid")
    if relative.parts and ":" in relative.parts[0]:
        raise SourceFetchError(source.original, "fetch.arxiv_source_invalid")
    return relative


def _result(content_path: Path, *, content_kind: ContentKind, content_name: str | None) -> FetchResult:
    return FetchResult(
        fetched_at=datetime.now(timezone.utc),
        content_kind=content_kind,
        content_name=content_name,
        content_digest=digest_content(content_path),
    )
