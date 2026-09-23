# apiscope/source.py
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias
from urllib.parse import SplitResult, urlsplit, urlunsplit

from apiscope.schema import DocumentType


class SourceParseReason(StrEnum):
    SOURCE_EMPTY = "source.parse.source_empty"
    LOCATION_INVALID = "source.parse.location_invalid"
    FILESYSTEM_PATH_INVALID = "source.parse.filesystem_path_invalid"
    FILESYSTEM_PATH_REQUIRED = "source.parse.filesystem_path_required"
    UNSUPPORTED_SCHEME = "source.parse.unsupported_scheme"
    REMOTE_HOST_MISSING = "source.parse.remote_host_missing"
    CREDENTIALS_UNSUPPORTED = "source.parse.credentials_unsupported"
    FRAGMENTS_UNSUPPORTED = "source.parse.fragments_unsupported"


_REMOTE_SCHEMES: dict[DocumentType, frozenset[str]] = {
    "filesystem": frozenset(),
    "repo": frozenset({"file", "git", "http", "https", "ssh"}),
    "openapi": frozenset({"http", "https"}),
    "rfc": frozenset({"http", "https"}),
    "llmstxt": frozenset({"http", "https"}),
}


@dataclass(frozen=True, slots=True)
class LocalSource:
    path: Path


@dataclass(frozen=True, slots=True)
class RemoteSource:
    url: str


SourceLocation: TypeAlias = LocalSource | RemoteSource


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    doc_type: DocumentType
    original: str
    canonical: str
    location: SourceLocation


class SourceResolutionError(ValueError):
    def __init__(
        self,
        source: str,
        reason_code: SourceParseReason,
        values: Mapping[str, object] | None = None,
    ) -> None:
        self.source = source
        self.reason_code = reason_code.value
        self.values = {} if values is None else dict(values)
        super().__init__(self.reason_code)


def parse_source(doc_type: DocumentType, source: str, *, base_dir: Path) -> SourceIdentity:
    value = source.strip()
    if not value:
        raise SourceResolutionError(source, SourceParseReason.SOURCE_EMPTY)

    try:
        parsed = urlsplit(value)
    except ValueError as error:
        reason = (
            SourceParseReason.FILESYSTEM_PATH_INVALID
            if doc_type == "filesystem"
            else SourceParseReason.LOCATION_INVALID
        )
        raise SourceResolutionError(source, reason, {"detail": str(error)}) from error

    if doc_type == "filesystem":
        if parsed.scheme:
            raise SourceResolutionError(source, SourceParseReason.FILESYSTEM_PATH_REQUIRED)
        return _local_source(doc_type, source, value, base_dir)

    if parsed.scheme:
        scheme = parsed.scheme.lower()
        if scheme not in _REMOTE_SCHEMES[doc_type]:
            raise SourceResolutionError(source, SourceParseReason.UNSUPPORTED_SCHEME, {"scheme": parsed.scheme})
        if not parsed.netloc:
            raise SourceResolutionError(source, SourceParseReason.REMOTE_HOST_MISSING)
        if parsed.username is not None or parsed.password is not None:
            raise SourceResolutionError(source, SourceParseReason.CREDENTIALS_UNSUPPORTED)
        if parsed.fragment:
            raise SourceResolutionError(source, SourceParseReason.FRAGMENTS_UNSUPPORTED)
        try:
            canonical = _canonical_url(parsed, scheme)
        except ValueError as error:
            raise SourceResolutionError(source, SourceParseReason.LOCATION_INVALID, {"detail": str(error)}) from error
        return SourceIdentity(
            doc_type=doc_type,
            original=source,
            canonical=canonical,
            location=RemoteSource(url=canonical),
        )

    return _local_source(doc_type, source, value, base_dir)


def _local_source(doc_type: DocumentType, original: str, value: str, base_dir: Path) -> SourceIdentity:
    try:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        reason = (
            SourceParseReason.FILESYSTEM_PATH_INVALID
            if doc_type == "filesystem"
            else SourceParseReason.LOCATION_INVALID
        )
        raise SourceResolutionError(original, reason, {"detail": str(error)}) from error
    return SourceIdentity(
        doc_type=doc_type,
        original=original,
        canonical=resolved.as_posix(),
        location=LocalSource(path=resolved),
    )


def _canonical_url(parsed: SplitResult, scheme: str) -> str:
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError("remote host is missing")
    host = hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, host, path, parsed.query, ""))


__all__ = [
    "LocalSource",
    "RemoteSource",
    "SourceIdentity",
    "SourceLocation",
    "SourceParseReason",
    "SourceResolutionError",
    "parse_source",
]
