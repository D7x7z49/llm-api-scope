# apiscope/sync/_lib/llmstxt/fetcher.py
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx2

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
        except (OSError, ValueError, httpx2.HTTPError) as error:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
        if content_kind != "file" or index_name is None:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": "the index is not a file"})

        base, index_dir = _index_base(source)
        index_path = content_path / index_name
        try:
            index_text = index_path.read_text(encoding="utf-8")
            index_bytes = index_path.read_bytes()
        except (OSError, UnicodeError) as error:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
        index_path.unlink(missing_ok=True)

        digests: dict[str, str] = {index_name: _store_body(content_path, index_bytes)}
        page_routes: list[str] = []
        for link in _links(index_text):
            target = urljoin(base, link)
            try:
                route = _route(base, target)
                data = _page_bytes(target, index_dir, proxy=proxy, no_proxy=no_proxy)
            except (OSError, ValueError, httpx2.HTTPError):
                continue
            if route == index_name:
                continue
            digests[route] = _store_body(content_path, data)
            page_routes.append(route)

        return FetchResult(
            fetched_at=datetime.now(timezone.utc),
            content_kind="directory",
            content_name=None,
            content_digest=digest_content(content_path),
            manifest=_tree_manifest(_logical_leaves(digests, page_routes)),
        )


def _store_body(content_path: Path, data: bytes) -> str:
    digest = sha256(data).hexdigest()
    body_path = content_path / digest
    if not body_path.exists():
        body_path.write_bytes(data)
    return digest


# a page route that is also a parent becomes an index leaf, so the tree stays a tree.
def _logical_leaves(digests: dict[str, str], page_routes: list[str]) -> dict[str, str]:
    sections: set[str] = set()
    for route in page_routes:
        parts = route.split("/")
        for length in range(1, len(parts)):
            sections.add("/".join(parts[:length]))

    leaves: dict[str, str] = {}
    for route, digest in digests.items():
        leaves[f"{route}/index" if route in sections else route] = digest
    return leaves


# a Merkle map over the logical tree; the same encoding as the generic content manifest.
def _tree_manifest(leaves: dict[str, str]) -> dict[str, str]:
    leaf_keys = set(leaves)
    manifest = dict(leaves)
    nodes: set[str] = set()
    for key in leaves:
        parts = key.split("/")
        for length in range(1, len(parts) + 1):
            nodes.add("/".join(parts[:length]))

    children: dict[str, list[str]] = {}
    for node in nodes:
        children.setdefault(node.rpartition("/")[0], []).append(node)

    for node in sorted(nodes, key=lambda value: value.count("/"), reverse=True):
        if node in manifest:
            continue
        manifest[node] = _node_digest(children.get(node, []), manifest, leaf_keys)
    manifest["."] = _node_digest(children.get("", []), manifest, leaf_keys)
    return manifest


def _node_digest(children: list[str], manifest: dict[str, str], leaf_keys: set[str]) -> str:
    digest = sha256()
    for child in sorted(children):
        name = child.rpartition("/")[2]
        kind = "f" if child in leaf_keys else "d"
        digest.update(kind.encode("ascii"))
        digest.update(b"\0")
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(manifest[child].encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


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
