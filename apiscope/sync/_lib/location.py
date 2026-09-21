# apiscope/sync/_lib/location.py
from __future__ import annotations

from pathlib import Path
from urllib.parse import SplitResult, urlsplit, urlunsplit

from apiscope.sync._lib.errors import SourceLocationError
from apiscope.sync._lib.schema import LocalSource, RemoteSource, SourceLocation


def parse_local_or_remote(
    source: str,
    *,
    base_dir: Path,
    remote_schemes: frozenset[str],
) -> tuple[str, SourceLocation]:
    value = source.strip()
    if not value:
        raise SourceLocationError("parse.source_empty")

    parsed = urlsplit(value)
    if parsed.scheme:
        scheme = parsed.scheme.lower()
        if scheme not in remote_schemes:
            raise SourceLocationError("parse.unsupported_scheme", {"scheme": parsed.scheme})
        if not parsed.netloc:
            raise SourceLocationError("parse.remote_host_missing")
        if parsed.username is not None or parsed.password is not None:
            raise SourceLocationError("parse.credentials_unsupported")
        if parsed.fragment:
            raise SourceLocationError("parse.fragments_unsupported")
        canonical = _canonical_url(parsed, scheme)
        return canonical, RemoteSource(url=canonical)

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    resolved = path.resolve(strict=False)
    return resolved.as_posix(), LocalSource(path=resolved)


def _canonical_url(parsed: SplitResult, scheme: str) -> str:
    hostname = parsed.hostname
    if hostname is None:
        raise SourceLocationError("parse.remote_host_missing")
    host = hostname.lower()
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, host, path, parsed.query, ""))
