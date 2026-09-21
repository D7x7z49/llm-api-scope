# apiscope/sync/_lib/transport.py
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Final
from urllib.parse import unquote, urlsplit

import httpx

from apiscope.sync._lib.cache import digest_content
from apiscope.sync._lib.errors import TransportError
from apiscope.sync._lib.schema import ContentKind, LocalSource, RemoteSource, SourceLocation

DEFAULT_REMOTE_CONTENT_NAME: Final = "document"
HTTP_TIMEOUT_SECONDS: Final = 30.0


def fetch_location(
    location: SourceLocation,
    *,
    destination: Path,
    proxy: str | None = None,
) -> tuple[ContentKind, str | None, str]:
    content_path = destination / "content"
    content_path.mkdir(parents=True, exist_ok=True)
    if isinstance(location, LocalSource):
        content_kind, content_name = _copy_local(location.path, content_path)
    else:
        content_kind, content_name = _fetch_remote(location, content_path, proxy=proxy)
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
    source: RemoteSource,
    content_path: Path,
    *,
    proxy: str | None,
) -> tuple[ContentKind, str]:
    name = _remote_name(source.url)
    if proxy is None:
        client = httpx.Client(
            follow_redirects=True,
            timeout=HTTP_TIMEOUT_SECONDS,
            trust_env=False,
        )
    else:
        client = httpx.Client(
            follow_redirects=True,
            timeout=HTTP_TIMEOUT_SECONDS,
            proxy=proxy,
            trust_env=False,
        )
    with client:
        response = client.get(source.url)
        response.raise_for_status()
    (content_path / name).write_bytes(response.content)
    return "file", name


def _remote_name(url: str) -> str:
    name = Path(unquote(urlsplit(url).path)).name
    if not name or name in {".", ".."}:
        return DEFAULT_REMOTE_CONTENT_NAME
    return name
