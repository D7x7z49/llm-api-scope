# apiscope/sync/_lib/transport.py
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Final
from urllib.parse import unquote, urlsplit

import httpx2

from apiscope.cache import digest_content
from apiscope.sync._lib.errors import TransportError
from apiscope.sync._lib.schema import ContentKind, LocalLocation, RemoteLocation, SourceLocation

DEFAULT_REMOTE_CONTENT_NAME: Final = "document"
HTTP_TIMEOUT_SECONDS: Final = 30.0


def fetch_location(
    location: SourceLocation,
    *,
    destination: Path,
    proxy: str | None = None,
    no_proxy: str | None = None,
) -> tuple[ContentKind, str | None, str]:
    content_path = destination / "content"
    content_path.mkdir(parents=True, exist_ok=True)
    if isinstance(location, LocalLocation):
        content_kind, content_name = _copy_local(location.path, content_path)
    else:
        content_kind, content_name = _fetch_remote(location, content_path, proxy=proxy, no_proxy=no_proxy)
    return content_kind, content_name, digest_content(content_path)


def _copy_local(source: Path, content_path: Path) -> tuple[ContentKind, str | None]:
    if not source.exists():
        raise TransportError("fetch.source_path_missing", {"path": str(source)})
    if source.is_dir():
        for child in source.iterdir():
            target = content_path / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                shutil.copy2(child, target)
        return "directory", None

    name = source.name or DEFAULT_REMOTE_CONTENT_NAME
    shutil.copy2(source, content_path / name)
    return "file", name


def _fetch_remote(
    source: RemoteLocation,
    content_path: Path,
    *,
    proxy: str | None,
    no_proxy: str | None,
) -> tuple[ContentKind, str]:
    name = _remote_name(source.url)
    (content_path / name).write_bytes(fetch_remote_bytes(source.url, proxy=proxy, no_proxy=no_proxy))
    return "file", name


def fetch_remote_bytes(url: str, *, proxy: str | None = None, no_proxy: str | None = None) -> bytes:
    with _client(proxy, no_proxy, url) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


# the program reads the proxy only from configuration; a configured proxy is used
# unless the target host is in the configured bypass list.
def _client(proxy: str | None, no_proxy: str | None, url: str) -> httpx2.Client:
    if not proxy or _is_bypassed(url, no_proxy):
        return httpx2.Client(follow_redirects=True, timeout=HTTP_TIMEOUT_SECONDS, trust_env=False)
    return httpx2.Client(follow_redirects=True, timeout=HTTP_TIMEOUT_SECONDS, proxy=proxy, trust_env=False)


def _is_bypassed(url: str, no_proxy: str | None) -> bool:
    if not no_proxy:
        return False
    hostname = urlsplit(url).hostname
    if hostname is None:
        return False
    host = hostname.lower()
    for raw in no_proxy.split(","):
        pattern = raw.strip().lower().lstrip(".")
        if not pattern:
            continue
        if pattern == "*" or host == pattern or host.endswith(f".{pattern}"):
            return True
    return False


def _remote_name(url: str) -> str:
    name = Path(unquote(urlsplit(url).path)).name
    if not name or name in {".", ".."}:
        return DEFAULT_REMOTE_CONTENT_NAME
    return name
