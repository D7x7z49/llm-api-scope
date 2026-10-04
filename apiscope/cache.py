# apiscope/cache.py
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
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
CACHE_MANIFEST_FILENAME: Final = "manifest.json"
# the cache directory name is a short prefix of the source digest
CACHE_DIGEST_MIN_LENGTH: Final = 7

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
    source_digest: str = Field(min_length=1)
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


# the source projection: a pure function of the canonical source string
# it is the cache identity and is not the Merkle root of the content
def source_digest(canonical_source: str) -> str:
    return sha256(canonical_source.encode("utf-8")).hexdigest()


# return the existing entry for the source, or the default short name
# the short name is a display form; the source digest is the real identity
def cache_path(cache_root: Path, canonical_source: str) -> Path:
    existing = find_cache_entry(cache_root, canonical_source)
    if existing is not None:
        return existing
    return cache_root / source_digest(canonical_source)[:CACHE_DIGEST_MIN_LENGTH]


# find the entry whose stored source digest matches the source
# match on the full digest, so a short directory name stays unambiguous
def find_cache_entry(cache_root: Path, canonical_source: str) -> Path | None:
    digest = source_digest(canonical_source)
    for entry in _cache_entries(cache_root):
        metadata = _read_cache_metadata(entry)
        if metadata is not None and metadata.source_digest == digest:
            return entry
    return None


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
    expected_digest: str | None = None,
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
        if expected_digest is not None and metadata.source_digest != expected_digest:
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


def build_manifest(content_path: Path) -> dict[str, str]:
    root = content_path.resolve()
    manifest: dict[str, str] = {}
    for file in sorted(path for path in root.rglob("*") if path.is_file()):
        manifest[file.relative_to(root).as_posix()] = _hash_file(file)
    directories = [root, *(path for path in root.rglob("*") if path.is_dir())]
    for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        digest = sha256()
        for child in sorted(directory.iterdir(), key=lambda path: path.name):
            key = child.relative_to(root).as_posix()
            kind = "d" if child.is_dir() else "f"
            digest.update(kind.encode("ascii"))
            digest.update(b"\0")
            digest.update(child.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(manifest.get(key, "").encode("ascii"))
            digest.update(b"\0")
        manifest[directory.relative_to(root).as_posix()] = digest.hexdigest()
    return manifest


def write_manifest(path: Path, manifest: Mapping[str, str]) -> None:
    manifest_path = path / CACHE_MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextmanager
def staging_cache(cache_root: Path, canonical_source: str) -> Iterator[Path]:
    cache_root.mkdir(parents=True, exist_ok=True)
    final_path = _prepare_cache_entry(cache_root, canonical_source)
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
    return _manifest_is_valid(path.parent)


def _manifest_is_valid(entry: Path) -> bool:
    manifest_path = entry / CACHE_MANIFEST_FILENAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and all(
        isinstance(key, str) and isinstance(value, str) for key, value in manifest.items()
    )


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


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


# reuse an existing entry or choose the shortest unique prefix
# colliding entries extend together
def _prepare_cache_entry(cache_root: Path, canonical_source: str) -> Path:
    existing = find_cache_entry(cache_root, canonical_source)
    if existing is not None:
        return existing

    digest = source_digest(canonical_source)
    known: dict[str, Path] = {}
    for entry in _cache_entries(cache_root):
        metadata = _read_cache_metadata(entry)
        if metadata is not None:
            known[metadata.source_digest] = entry

    names = _assign_cache_names([*known, digest])
    for known_digest, entry in known.items():
        target = cache_root / names[known_digest]
        _rename_entry(entry, target)
    return cache_root / names[digest]


# assign the shortest prefix that distinguishes each digest from the others
def _assign_cache_names(digests: list[str]) -> dict[str, str]:
    names: dict[str, str] = {}
    for digest in digests:
        length = CACHE_DIGEST_MIN_LENGTH
        while length < len(digest):
            prefix = digest[:length]
            if all(other[:length] != prefix for other in digests if other != digest):
                break
            length += 1
        names[digest] = digest[:length]
    return names


# rename an entry, moving any target aside first to avoid overwriting it
def _rename_entry(entry: Path, target: Path) -> None:
    if entry == target:
        return
    temporary = target.with_name(f".{target.name}.rename")
    _remove_path(temporary)
    if target.exists():
        target.rename(temporary)
    try:
        entry.rename(target)
    except OSError:
        if temporary.exists():
            temporary.rename(target)
        raise
    _remove_path(temporary)


# return the directories that hold a cache entry, in name order
def _cache_entries(cache_root: Path) -> list[Path]:
    if not cache_root.is_dir():
        return []
    entries = [child for child in cache_root.iterdir() if child.is_dir() and _is_hex_name(child.name)]
    return sorted(entries, key=lambda path: path.name)


# read the metadata of an entry, or None when the entry is unreadable
def _read_cache_metadata(entry: Path) -> CacheMetadata | None:
    try:
        content = (entry / CACHE_METADATA_FILENAME).read_text(encoding="utf-8")
        return CacheMetadata.model_validate_json(content)
    except (OSError, TypeError, ValueError, ValidationError):
        return None


def _is_hex_name(name: str) -> bool:
    return bool(name) and all(character in "0123456789abcdef" for character in name)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()
