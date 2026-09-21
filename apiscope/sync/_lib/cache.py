# apiscope/sync/_lib/cache.py
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

from pydantic import ValidationError

from apiscope.sync._lib.schema import CacheMetadata, FetchResult, ParsedSource

CACHE_CONTENT_DIRECTORY: Final = "content"
CACHE_FORMAT_VERSION: Final = "1"
CACHE_METADATA_FILENAME: Final = "metadata.json"
CacheState = Literal["missing", "fresh", "expired", "invalid"]


@dataclass(frozen=True, slots=True)
class CacheInspection:
    state: CacheState
    metadata: CacheMetadata | None = None


def cache_path(cache_root: Path, canonical_source: str) -> Path:
    identity = sha256(canonical_source.encode("utf-8")).hexdigest()
    return cache_root / identity


def inspect_cache(
    path: Path,
    *,
    ttl_days: int,
    now: datetime | None = None,
) -> CacheInspection:
    if not path.exists():
        return CacheInspection("missing")

    metadata_path = path / CACHE_METADATA_FILENAME
    content_path = path / CACHE_CONTENT_DIRECTORY
    try:
        metadata = CacheMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
        if not _content_is_valid(content_path, metadata):
            return CacheInspection("invalid")
    except (OSError, TypeError, ValueError, ValidationError):
        return CacheInspection("invalid")

    current = datetime.now(timezone.utc) if now is None else _as_utc(now)
    fetched_at = _as_utc(metadata.fetched_at)
    fresh_until = fetched_at + timedelta(days=ttl_days)
    state: CacheState = "fresh" if current <= fresh_until else "expired"
    return CacheInspection(state, metadata)


def write_metadata(path: Path, source: ParsedSource, result: FetchResult) -> CacheMetadata:
    metadata = CacheMetadata(
        format_version=CACHE_FORMAT_VERSION,
        doc_type=source.doc_type,
        source=source.canonical,
        fetched_at=result.fetched_at,
        content_kind=result.content_kind,
        content_name=result.content_name,
        content_digest=result.content_digest,
    )
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


def digest_content(path: Path) -> str:
    digest = sha256()
    if path.is_file():
        _update_file_digest(digest, Path(path.name), path)
        return digest.hexdigest()

    for child in sorted(path.rglob("*")):
        if child.is_file():
            _update_file_digest(digest, child.relative_to(path), child)
    return digest.hexdigest()


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
    hasher = digest
    hasher.update(relative_path.as_posix().encode("utf-8"))
    hasher.update(b"\0")
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            hasher.update(chunk)
    hasher.update(b"\0")


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
