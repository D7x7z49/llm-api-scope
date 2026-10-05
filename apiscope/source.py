# apiscope/source.py
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, Protocol, TypeAlias
from urllib.parse import SplitResult, urlsplit, urlunsplit

from pydantic import ConfigDict, Field

from apiscope.schema import DocumentType, StrictSchemaModel


class SourceParseReason(StrEnum):
    SOURCE_EMPTY = "source.parse.source_empty"
    SOURCE_WHITESPACE = "source.parse.source_whitespace"
    PATH_HOME_UNSUPPORTED = "source.parse.path_home_unsupported"
    LOCATION_INVALID = "source.parse.location_invalid"
    FILESYSTEM_PATH_INVALID = "source.parse.filesystem_path_invalid"
    FILESYSTEM_PATH_REQUIRED = "source.parse.filesystem_path_required"
    UNSUPPORTED_SCHEME = "source.parse.unsupported_scheme"
    REMOTE_HOST_MISSING = "source.parse.remote_host_missing"
    CREDENTIALS_UNSUPPORTED = "source.parse.credentials_unsupported"
    FRAGMENTS_UNSUPPORTED = "source.parse.fragments_unsupported"
    REF_INVALID = "source.parse.ref_invalid"
    SUBPATH_INVALID = "source.parse.subpath_invalid"
    RFC_NUMBER_INVALID = "source.parse.rfc_number_invalid"
    LOCAL_FORM_UNSUPPORTED = "source.parse.local_form_unsupported"
    SCP_UNSUPPORTED = "source.parse.scp_unsupported"


_REMOTE_SCHEMES: dict[DocumentType, frozenset[str]] = {
    "filesystem": frozenset(),
    "repo": frozenset({"http", "https"}),
    "openapi": frozenset({"http", "https"}),
    "rfc": frozenset(),
    "llmstxt": frozenset({"http", "https"}),
}

# only these types accept a local path
_LOCAL_TYPES: frozenset[DocumentType] = frozenset({"filesystem", "repo", "openapi"})
# the repository path starts after the git suffix, as in repository.git/docs
_REPO_PATH_MARKER = ".git/"
# the rfc number form prefers the xml form; the fetcher falls back to text
_RFC_TARGET = "https://www.rfc-editor.org/rfc/rfc{number}.xml"
# an scp-style location is out of scope and is not a local path
_SCP_LOCATION = re.compile(r"^[^/@:]+@[^/@:]+:")


@dataclass(frozen=True, slots=True)
class LocalLocation:
    path: Path


@dataclass(frozen=True, slots=True)
class RemoteLocation:
    url: str


SourceLocation: TypeAlias = LocalLocation | RemoteLocation


# the common identity: one registered link plus its fetch location
class SourceIdentity(StrictSchemaModel):
    model_config = ConfigDict(frozen=True)

    original: str
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
    if source != source.strip():
        raise SourceResolutionError(source, SourceParseReason.SOURCE_WHITESPACE)
    if not source:
        raise SourceResolutionError(source, SourceParseReason.SOURCE_EMPTY)
    return _PARSERS[doc_type](source, base_dir=base_dir)


def _parse_filesystem(source: str, *, base_dir: Path) -> FilesystemSource:
    location = _resolve_location("filesystem", source, source, base_dir)
    return FilesystemSource(original=source, location=location)


def _parse_repo(source: str, *, base_dir: Path) -> RepoSource:
    if _SCP_LOCATION.match(source):
        raise SourceResolutionError(source, SourceParseReason.SCP_UNSUPPORTED)
    location_text, ref = _split_repo_ref(source)
    location_text, subpath = _split_repo_subpath(location_text, base_dir)
    if ref is not None:
        ref = _normalize_ref(source, ref)
    if subpath is not None:
        subpath = _validate_subpath(source, subpath)
    location = _resolve_location("repo", source, location_text, base_dir)
    return RepoSource(original=source, location=location, subpath=subpath, ref=ref)


def _parse_openapi(source: str, *, base_dir: Path) -> OpenapiSource:
    location = _resolve_location("openapi", source, source, base_dir)
    return OpenapiSource(original=source, location=location)


def _parse_rfc(source: str, *, base_dir: Path) -> RfcSource:
    if not source.isascii() or not source.isdecimal():
        raise SourceResolutionError(source, SourceParseReason.RFC_NUMBER_INVALID, {"number": source})
    try:
        number = int(source)
    except ValueError as error:
        raise SourceResolutionError(source, SourceParseReason.RFC_NUMBER_INVALID, {"number": source}) from error
    if number <= 0:
        raise SourceResolutionError(source, SourceParseReason.RFC_NUMBER_INVALID, {"number": source})
    return RfcSource(
        original=source,
        location=RemoteLocation(url=_RFC_TARGET.format(number=number)),
    )


def _parse_llmstxt(source: str, *, base_dir: Path) -> LlmstxtSource:
    location = _resolve_location("llmstxt", source, source, base_dir)
    return LlmstxtSource(original=source, location=location)


_PARSERS: dict[DocumentType, SourceParser] = {
    "filesystem": _parse_filesystem,
    "repo": _parse_repo,
    "openapi": _parse_openapi,
    "rfc": _parse_rfc,
    "llmstxt": _parse_llmstxt,
}


# split the compact repo link at the final @ that follows the location
def _split_repo_ref(value: str) -> tuple[str, str | None]:
    last_at = value.rfind("@")
    if last_at == -1 or last_at < _authority_end(value):
        return value, None
    return value[:last_at], value[last_at + 1 :]


# the offset where the URL authority ends; zero for a local path
def _authority_end(value: str) -> int:
    marker = value.find("://")
    if marker == -1:
        return 0
    slash = value.find("/", marker + 3)
    if slash == -1:
        return len(value)
    return slash


# split the repository path from the git location at the .git suffix
# a local location without that suffix falls back to the nearest git root
def _split_repo_subpath(value: str, base_dir: Path) -> tuple[str, str | None]:
    marker = value.find(_REPO_PATH_MARKER, _authority_end(value))
    if marker != -1:
        end = marker + len(".git")
        return value[:end], value[end + 1 :]
    return _split_local_repo_subpath(value, base_dir)


def _split_local_repo_subpath(value: str, base_dir: Path) -> tuple[str, str | None]:
    if "://" in value:
        return value, None
    try:
        path = Path(value)
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
    if not ref or ref != ref.strip() or ref.startswith("-") or any(character.isspace() for character in ref):
        raise SourceResolutionError(source, SourceParseReason.REF_INVALID)
    return ref


def _validate_subpath(source: str, subpath: str) -> str:
    path = PurePosixPath(subpath)
    if subpath != subpath.strip("/") or not subpath or subpath == "." or path.is_absolute() or ".." in path.parts:
        raise SourceResolutionError(source, SourceParseReason.SUBPATH_INVALID, {"detail": subpath})
    return subpath


# resolve a value to its fetch location
# the registered link stays the identity; this only builds the transport target
def _resolve_location(
    doc_type: DocumentType,
    source: str,
    value: str,
    base_dir: Path,
) -> SourceLocation:
    # urlsplit treats a Windows drive letter as a URI scheme.
    if doc_type in _LOCAL_TYPES and PureWindowsPath(value).drive:
        return _local_location(doc_type, source, value, base_dir)

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

    if not parsed.scheme and doc_type not in _LOCAL_TYPES:
        raise SourceResolutionError(source, SourceParseReason.LOCAL_FORM_UNSUPPORTED)

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
            url = _transport_url(parsed, scheme)
        except ValueError as error:
            raise SourceResolutionError(source, SourceParseReason.LOCATION_INVALID, {"detail": str(error)}) from error
        return RemoteLocation(url=url)

    return _local_location(doc_type, source, value, base_dir)


def _local_location(
    doc_type: DocumentType,
    original: str,
    value: str,
    base_dir: Path,
) -> LocalLocation:
    if value.startswith("~"):
        raise SourceResolutionError(original, SourceParseReason.PATH_HOME_UNSUPPORTED, {"path": value})
    try:
        path = Path(value)
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
    return LocalLocation(path=resolved)


# build the transport URL from a parsed remote location
# host case and the default path are transport details, not identity
def _transport_url(parsed: SplitResult, scheme: str) -> str:
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


# the cache identity: the registered link, scoped when it is relative
# a relative local link gains meaning from its project root, so that root is part of the key
def cache_identity(source: Source, *, base_dir: Path) -> str:
    if isinstance(source.location, RemoteLocation):
        return source.original
    if is_absolute_path(source.original):
        return source.original
    return f"{base_dir.as_posix()}\0{source.original}"


# a local path is absolute on the running platform or as a Windows path
# a local source with no scheme is a local path; a remote link keeps its scheme
def is_absolute_path(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or Path(value).is_absolute()


def is_local_form(doc_type: DocumentType, source: str) -> bool:
    return doc_type in _LOCAL_TYPES and "://" not in source


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
    "cache_identity",
    "is_absolute_path",
    "is_local_form",
    "parse_source",
]
