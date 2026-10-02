# apiscope/source.py
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Protocol, TypeAlias
from urllib.parse import SplitResult, urlsplit, urlunsplit

from pydantic import ConfigDict, Field

from apiscope.schema import DocumentType, StrictSchemaModel


class SourceParseReason(StrEnum):
    SOURCE_EMPTY = "source.parse.source_empty"
    LOCATION_INVALID = "source.parse.location_invalid"
    FILESYSTEM_PATH_INVALID = "source.parse.filesystem_path_invalid"
    FILESYSTEM_PATH_REQUIRED = "source.parse.filesystem_path_required"
    UNSUPPORTED_SCHEME = "source.parse.unsupported_scheme"
    REMOTE_HOST_MISSING = "source.parse.remote_host_missing"
    CREDENTIALS_UNSUPPORTED = "source.parse.credentials_unsupported"
    FRAGMENTS_UNSUPPORTED = "source.parse.fragments_unsupported"
    REF_INVALID = "source.parse.ref_invalid"
    SUBPATH_INVALID = "source.parse.subpath_invalid"


_REMOTE_SCHEMES: dict[DocumentType, frozenset[str]] = {
    "filesystem": frozenset(),
    "repo": frozenset({"file", "git", "http", "https", "ssh"}),
    "openapi": frozenset({"http", "https"}),
    "rfc": frozenset({"http", "https"}),
    "llmstxt": frozenset({"http", "https"}),
}

# a scp-style git location keeps its user@ prefix and is not a URL scheme
_SCP_LOCATION = re.compile(r"^[^/@:]+@[^/@:]+:")
# the repository path starts after the git suffix, as in repository.git/docs
_REPO_PATH_MARKER = ".git/"
_ENCODED_AT = "%40"


@dataclass(frozen=True, slots=True)
class LocalLocation:
    path: Path


@dataclass(frozen=True, slots=True)
class RemoteLocation:
    url: str


SourceLocation: TypeAlias = LocalLocation | RemoteLocation


# the common identity: the address a source keeps in the cache
class SourceIdentity(StrictSchemaModel):
    model_config = ConfigDict(frozen=True)

    original: str
    canonical: str
    location: SourceLocation


# one model per document type; doc_type is the union discriminator
class FilesystemSource(SourceIdentity):
    doc_type: Literal["filesystem"] = "filesystem"


class RepoSource(SourceIdentity):
    doc_type: Literal["repo"] = "repo"
    subpath: str | None = None
    ref: str | None = None


class OpenapiSource(SourceIdentity):
    doc_type: Literal["openapi"] = "openapi"


class RfcSource(SourceIdentity):
    doc_type: Literal["rfc"] = "rfc"


class LlmstxtSource(SourceIdentity):
    doc_type: Literal["llmstxt"] = "llmstxt"


Source: TypeAlias = Annotated[
    FilesystemSource | RepoSource | OpenapiSource | RfcSource | LlmstxtSource,
    Field(discriminator="doc_type"),
]


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


class SourceParser(Protocol):
    def __call__(self, source: str, *, base_dir: Path) -> Source: ...


def parse_source(doc_type: DocumentType, source: str, *, base_dir: Path) -> Source:
    if not source.strip():
        raise SourceResolutionError(source, SourceParseReason.SOURCE_EMPTY)
    return _PARSERS[doc_type](source, base_dir=base_dir)


def _parse_filesystem(source: str, *, base_dir: Path) -> FilesystemSource:
    canonical, location = _resolve_location("filesystem", source, source.strip(), base_dir)
    return FilesystemSource(original=source, canonical=canonical, location=location)


def _parse_repo(source: str, *, base_dir: Path) -> RepoSource:
    value = source.strip()
    location_text, ref = _split_repo_ref(value)
    location_text, subpath = _split_repo_subpath(location_text, base_dir)
    if ref is not None:
        ref = _normalize_ref(source, ref)
    if subpath is not None:
        subpath = _normalize_subpath(source, subpath)
    canonical, location = _resolve_location("repo", source, location_text, base_dir)
    if subpath is not None:
        canonical = f"{canonical}/{subpath}"
    if ref is not None:
        canonical = f"{canonical}@{ref}"
    return RepoSource(original=source, canonical=canonical, location=location, subpath=subpath, ref=ref)


def _parse_openapi(source: str, *, base_dir: Path) -> OpenapiSource:
    canonical, location = _resolve_location("openapi", source, source.strip(), base_dir)
    return OpenapiSource(original=source, canonical=canonical, location=location)


def _parse_rfc(source: str, *, base_dir: Path) -> RfcSource:
    canonical, location = _resolve_location("rfc", source, source.strip(), base_dir)
    return RfcSource(original=source, canonical=canonical, location=location)


def _parse_llmstxt(source: str, *, base_dir: Path) -> LlmstxtSource:
    canonical, location = _resolve_location("llmstxt", source, source.strip(), base_dir)
    return LlmstxtSource(original=source, canonical=canonical, location=location)


_PARSERS: dict[DocumentType, SourceParser] = {
    "filesystem": _parse_filesystem,
    "repo": _parse_repo,
    "openapi": _parse_openapi,
    "rfc": _parse_rfc,
    "llmstxt": _parse_llmstxt,
}


# split the compact repo link at the final unescaped @, keep a scp user@ prefix
def _split_repo_ref(value: str) -> tuple[str, str | None]:
    scp = _SCP_LOCATION.match(value)
    scp_at = scp.group(0).index("@") if scp is not None else -1
    last_at = value.rfind("@")
    if last_at == -1 or last_at == scp_at:
        return value, None
    return value[:last_at], value[last_at + 1 :]


# split the repository path from the git location at the .git suffix
# a local location without that suffix falls back to the nearest git root
def _split_repo_subpath(value: str, base_dir: Path) -> tuple[str, str | None]:
    marker = value.find(_REPO_PATH_MARKER)
    if marker != -1:
        end = marker + len(".git")
        return value[:end], value[end + 1 :]
    return _split_local_repo_subpath(value, base_dir)


def _split_local_repo_subpath(value: str, base_dir: Path) -> tuple[str, str | None]:
    if "://" in value or _SCP_LOCATION.match(value):
        return value, None
    try:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return value, None
    candidate = path
    while candidate != candidate.parent:
        if (candidate / ".git").exists():
            if candidate == path:
                return value, None
            return candidate.as_posix(), path.relative_to(candidate).as_posix()
        candidate = candidate.parent
    return value, None


def _normalize_ref(source: str, ref: str) -> str:
    value = ref.replace(_ENCODED_AT, "@")
    if not value or value != value.strip() or value.startswith("-") or any(character.isspace() for character in value):
        raise SourceResolutionError(source, SourceParseReason.REF_INVALID)
    return value


def _normalize_subpath(source: str, subpath: str) -> str:
    value = subpath.strip("/")
    path = PurePosixPath(value)
    if not value or value == "." or path.is_absolute() or ".." in path.parts:
        raise SourceResolutionError(source, SourceParseReason.SUBPATH_INVALID, {"detail": subpath})
    return value


# resolve a location to its canonical string and its typed location
def _resolve_location(
    doc_type: DocumentType,
    source: str,
    value: str,
    base_dir: Path,
) -> tuple[str, SourceLocation]:
    if doc_type == "repo" and _SCP_LOCATION.match(value):
        return value, RemoteLocation(url=value)

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
        return _local_location(doc_type, source, value, base_dir)

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
        return canonical, RemoteLocation(url=canonical)

    return _local_location(doc_type, source, value, base_dir)


def _local_location(
    doc_type: DocumentType,
    original: str,
    value: str,
    base_dir: Path,
) -> tuple[str, SourceLocation]:
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
    return resolved.as_posix(), LocalLocation(path=resolved)


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
    "FilesystemSource",
    "LlmstxtSource",
    "LocalLocation",
    "OpenapiSource",
    "RemoteLocation",
    "RepoSource",
    "RfcSource",
    "Source",
    "SourceIdentity",
    "SourceLocation",
    "SourceParseReason",
    "SourceResolutionError",
    "parse_source",
]
