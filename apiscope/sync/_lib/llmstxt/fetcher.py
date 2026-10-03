# apiscope/sync/_lib/llmstxt/fetcher.py
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

from apiscope.cache import CACHE_CONTENT_DIRECTORY, digest_content
from apiscope.sync._lib.errors import SourceFetchError, TransportError
from apiscope.sync._lib.schema import FetchResult, LocalLocation, ParsedSource, RemoteLocation
from apiscope.sync._lib.transport import fetch_location, fetch_remote_bytes

_LINK = re.compile(
    r"^\s*[-*]\s+\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)"
    r"(?:\s*:\s*(?P<description>.*))?\s*$"
)
_REMOTE_SCHEMES = {"http", "https"}


class LlmstxtFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
        no_proxy: str | None = None,
    ) -> FetchResult:
        content_path = destination / CACHE_CONTENT_DIRECTORY
        content_path.mkdir(parents=True, exist_ok=True)
        try:
            content_kind, index_name, _ = fetch_location(
                source.location, destination=destination, proxy=proxy, no_proxy=no_proxy
            )
        except TransportError as error:
            raise SourceFetchError(source.original, error.reason_code, error.values) from error
        except (OSError, ValueError, httpx.HTTPError) as error:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
        if content_kind != "file" or index_name is None:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": "the index is not a file"})

        base, index_dir = _index_base(source)
        try:
            index_text = (content_path / index_name).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
        for link in _links(index_text):
            target = urljoin(base, link)
            try:
                page = content_path / _route(base, target)
                data = _page_bytes(target, index_dir, proxy=proxy, no_proxy=no_proxy)
            except (OSError, ValueError, httpx.HTTPError):
                continue
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_bytes(data)

        return FetchResult(
            fetched_at=datetime.now(timezone.utc),
            content_kind="directory",
            content_name=None,
            content_digest=digest_content(content_path),
        )


def _index_base(source: ParsedSource) -> tuple[str, Path | None]:
    location = source.location
    if isinstance(location, RemoteLocation):
        return location.url, None
    if isinstance(location, LocalLocation):
        return str(location.path), location.path.parent
    raise ValueError("the llmstxt source is unsupported")


def _page_bytes(target: str, index_dir: Path | None, *, proxy: str | None, no_proxy: str | None) -> bytes:
    parts = urlsplit(target)
    if parts.scheme.lower() in _REMOTE_SCHEMES and parts.netloc:
        return fetch_remote_bytes(target, proxy=proxy, no_proxy=no_proxy)
    if index_dir is None:
        raise ValueError("a local link needs a local index")
    return Path(target).read_bytes()


def _links(text: str) -> list[str]:
    urls: list[str] = []
    for line in text.splitlines():
        match = _LINK.match(line)
        if match is not None:
            urls.append(match.group("url").strip())
    return urls


def _route(base: str, target: str) -> str:
    source_parts = urlsplit(base)
    target_parts = urlsplit(target)
    if target_parts.username is not None or target_parts.password is not None:
        raise ValueError("credentials unsupported")
    path = target_parts.path
    same_origin = (
        source_parts.scheme.lower() == target_parts.scheme.lower()
        and source_parts.netloc.lower() == target_parts.netloc.lower()
        and bool(target_parts.netloc)
    )
    if target_parts.netloc and not same_origin:
        path = f"{target_parts.netloc}/{path.lstrip('/')}"
    else:
        prefix = source_parts.path.rpartition("/")[0].rstrip("/")
        if prefix and (path == prefix or path.startswith(f"{prefix}/")):
            path = path[len(prefix) :]
    route = path.strip("/")
    if not route:
        return "index"
    if ".." in Path(route).parts:
        raise ValueError("unsafe route")
    return route
