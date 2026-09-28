# apiscope/cache.py
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Final, Iterator, Literal

from pydantic import Field, ValidationError

from apiscope.schema import DocumentType, StrictSchemaModel

# ==============================================================================
# constants
# ==============================================================================


CACHE_CONTENT_DIRECTORY: Final = "content"
CACHE_FORMAT_VERSION: Final = "1"
CACHE_METADATA_FILENAME: Final = "metadata.json"

# ==============================================================================
# types
# ==============================================================================


CacheState = Literal["missing", "fresh", "expired", "invalid"]
ContentKind = Literal["file", "directory"]

# ==============================================================================
# metadata
# ==============================================================================


class CacheMetadata(StrictSchemaModel):
    format_version: str = Field(min_length=1)
    doc_type: DocumentType
    source: str = Field(min_length=1)
    fetched_at: datetime
    content_kind: ContentKind
    content_name: str | None = None
    content_digest: str = Field(min_length=1)


# ==============================================================================
# state
# ==============================================================================


@dataclass(frozen=True, slots=True)
class CacheInspection:
    state: CacheState
    metadata: CacheMetadata | None = None


# ==============================================================================
# identity
# ==============================================================================


def cache_path(cache_root: Path, canonical_source: str) -> Path:
    identity = sha256(canonical_source.encode("utf-8")).hexdigest()
    return cache_root / identity


# ==============================================================================
# content
# ==============================================================================


def resolve_content_file(content: Path, metadata: CacheMetadata) -> Path | None:
    if metadata.content_kind != "file" or metadata.content_name is None:
        return None
    try:
        root = content.resolve(strict=True)
        path = (root / metadata.content_name).resolve(strict=True)
        path.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None
    return path if path.is_file() else None


# ==============================================================================
# inspection
# ==============================================================================


def inspect_cache(
    path: Path,
    *,
    ttl_days: int,
    now: datetime | None = None,
    expected_source: str | None = None,
    expected_doc_type: DocumentType | None = None,
) -> CacheInspection:
    if not path.exists():
        return CacheInspection("missing")

    metadata_path = path / CACHE_METADATA_FILENAME
    content_path = path / CACHE_CONTENT_DIRECTORY
    try:
        metadata = CacheMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
        if metadata.format_version != CACHE_FORMAT_VERSION:
            return CacheInspection("invalid")
        if expected_source is not None and metadata.source != expected_source:
            return CacheInspection("invalid")
        if expected_doc_type is not None and metadata.doc_type != expected_doc_type:
            return CacheInspection("invalid")
        if not _content_is_valid(content_path, metadata):
            return CacheInspection("invalid")
    except (OSError, TypeError, ValueError, ValidationError):
        return CacheInspection("invalid")

    current = datetime.now(timezone.utc) if now is None else _as_utc(now)
    fetched_at = _as_utc(metadata.fetched_at)
    fresh_until = fetched_at + timedelta(days=ttl_days)
    state: CacheState = "fresh" if current <= fresh_until else "expired"
    return CacheInspection(state, metadata)


# ==============================================================================
# publication
# ==============================================================================


def write_metadata(path: Path, metadata: CacheMetadata) -> CacheMetadata:
    metadata_path = path / CACHE_METADATA_FILENAME
    metadata_path.write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return metadata


@contextmanager
def staging_cache(cache_root: Path, canonical_source: str) -> Iterator[Path]:
    cache_root.mkdir(parents=True, exist_ok=True)
    final_path = cache_path(cache_root, canonical_source)
    staging_path = Path(tempfile.mkdtemp(prefix=f".{final_path.name}.", dir=cache_root))
    promoted = False
    try:
        yield staging_path
        _promote(staging_path, final_path)
        promoted = True
    finally:
        if not promoted:
            _remove_path(staging_path)


# ==============================================================================
# digest
# ==============================================================================


def digest_content(path: Path) -> str:
    digest = sha256()
    if path.is_file():
        _update_file_digest(digest, Path(path.name), path)
        return digest.hexdigest()

    for child in sorted(path.rglob("*")):
        if child.is_file():
            _update_file_digest(digest, child.relative_to(path), child)
    return digest.hexdigest()


# ==============================================================================
# private helpers
# ==============================================================================


def _content_is_valid(path: Path, metadata: CacheMetadata) -> bool:
    if not path.is_dir():
        return False
    if metadata.content_kind == "file":
        if metadata.content_name is None:
            return False
        content_file = path / metadata.content_name
        return content_file.parent == path and content_file.is_file()
    return True


def _update_file_digest(digest: hashlib._Hash, relative_path: Path, path: Path) -> None:
    digest.update(relative_path.as_posix().encode("utf-8"))
    digest.update(b"\0")
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    digest.update(b"\0")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _promote(staging_path: Path, final_path: Path) -> None:
    backup_path = final_path.with_name(f".{final_path.name}.backup")
    _remove_path(backup_path)
    if final_path.exists():
        os.replace(final_path, backup_path)
    try:
        os.replace(staging_path, final_path)
    except OSError:
        if backup_path.exists():
            os.replace(backup_path, final_path)
        raise
    _remove_path(backup_path)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()
