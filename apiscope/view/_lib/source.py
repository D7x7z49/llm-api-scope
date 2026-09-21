# apiscope/view/_lib/source.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import SplitResult, urlsplit, urlunsplit

from apiscope.schema import DocumentType
from apiscope.view._lib.errors import ViewSourceError

_REMOTE_SCHEMES: dict[DocumentType, frozenset[str]] = {
    "filesystem": frozenset(),
    "repo": frozenset({"file", "git", "http", "https", "ssh"}),
    "openapi": frozenset({"http", "https"}),
    "rfc": frozenset({"http", "https"}),
    "llmstxt": frozenset({"http", "https"}),
}


@dataclass(frozen=True, slots=True)
class ViewSource:
    doc_type: DocumentType
    original: str
    canonical: str


def parse_source(doc_type: DocumentType, source: str, *, base_dir: Path) -> ViewSource:
    value = source.strip()
    if not value:
        raise ViewSourceError("parse.source_empty")

    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise ViewSourceError("parse.location_invalid") from error

    if parsed.scheme:
        if parsed.scheme.lower() not in _REMOTE_SCHEMES[doc_type]:
            raise ViewSourceError("parse.unsupported_scheme", {"scheme": parsed.scheme})
        if not parsed.netloc:
            raise ViewSourceError("parse.remote_host_missing")
        if parsed.username is not None or parsed.password is not None:
            raise ViewSourceError("parse.credentials_unsupported")
        if parsed.fragment:
            raise ViewSourceError("parse.fragments_unsupported")
        canonical = _canonical_url(parsed, parsed.scheme.lower())
        return ViewSource(doc_type=doc_type, original=source, canonical=canonical)

    if doc_type != "filesystem" and not _REMOTE_SCHEMES[doc_type]:
        raise ViewSourceError("parse.unsupported_scheme")
    try:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise ViewSourceError("parse.location_invalid") from error
    return ViewSource(doc_type=doc_type, original=source, canonical=resolved.as_posix())


def _canonical_url(parsed: SplitResult, scheme: str) -> str:
    hostname = parsed.hostname
    if hostname is None:
        raise ViewSourceError("parse.remote_host_missing")
    host = hostname.lower()
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, host, path, parsed.query, ""))
