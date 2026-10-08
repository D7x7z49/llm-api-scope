# apiscope/bookmark/store.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from apiscope.bookmark.constants import (
    BOOKMARK_FILENAME,
    BOOKMARK_SCHEMA_FILENAME,
    BOOKMARK_SCHEMA_REF,
)
from apiscope.bookmark.errors import BookmarkError
from apiscope.bookmark.resolve import target_digest
from apiscope.bookmark.schema import BookmarkEntry, BookmarkFile
from apiscope.config import ensure_config_file, ensure_schema_file, load_config_file, save_config_file
from apiscope.context import RuntimeContext
from apiscope.gitignore import ensure_project_gitignore

# ==============================================================================
# storage paths
# ==============================================================================


def global_path(runtime: RuntimeContext) -> Path:
    return runtime.paths.home.root / BOOKMARK_FILENAME


def project_path(runtime: RuntimeContext) -> Path | None:
    if runtime.paths.project is None:
        return None
    return runtime.paths.project.config.parent / BOOKMARK_FILENAME


# a project entry shadows a global entry, so search the project layer first
def layers(runtime: RuntimeContext) -> tuple[Path, ...]:
    path = project_path(runtime)
    if path is None:
        return (global_path(runtime),)
    return (path, global_path(runtime))


# write into the project layer when one exists, otherwise into the global layer
def write_path(runtime: RuntimeContext) -> Path:
    path = project_path(runtime)
    if path is None or runtime.options.global_only:
        return global_path(runtime)
    return path


def _schema_path(target: Path) -> Path:
    return target.parent / "schema" / BOOKMARK_SCHEMA_FILENAME


# ==============================================================================
# persistence
# ==============================================================================


# load one layer without creating it, so a read command never writes
def _load_layer(path: Path) -> BookmarkFile:
    return cast(BookmarkFile, load_config_file(path, BookmarkFile, schema_ref=BOOKMARK_SCHEMA_REF))


def load_layer(path: Path) -> BookmarkFile:
    return _load_layer(path)


def save_layer(path: Path, data: BookmarkFile) -> None:
    _ensure_directory(path.parent)
    save_config_file(path, data)


# merge the layers, so a project id overrides a global id
def load_bookmarks(runtime: RuntimeContext) -> BookmarkFile:
    merged = _load_layer(global_path(runtime))
    path = project_path(runtime)
    if path is not None:
        project = _load_layer(path)
        merged.bookmarks = {**merged.bookmarks, **project.bookmarks}
    return merged


# prepare the layer and its schema before a write command
# a project layer also needs its state directory ignored by the project
# the read preflight creates no directories, so prepare them here
def ensure_bookmarks(runtime: RuntimeContext) -> BookmarkFile:
    target = write_path(runtime)
    _ensure_directory(target.parent)
    schema_path = _schema_path(target)
    _ensure_directory(schema_path.parent)
    ensure_schema_file(schema_path, BookmarkFile)
    project = runtime.paths.project
    if project is not None and target == project.config.parent / BOOKMARK_FILENAME:
        ensure_project_gitignore(project.gitignore)
    return cast(BookmarkFile, ensure_config_file(target, BookmarkFile, schema_ref=BOOKMARK_SCHEMA_REF))


def save_bookmarks(runtime: RuntimeContext, data: BookmarkFile) -> None:
    target = write_path(runtime)
    _ensure_directory(target.parent)
    save_config_file(target, data)


# the stored digest is the contract; status is derived and never persisted
def entry_status(
    runtime: RuntimeContext,
    entries: Mapping[str, BookmarkEntry],
    entry: BookmarkEntry,
    _seen: frozenset[str] = frozenset(),
) -> str:
    if entry.removed:
        return "removed"
    if entry.mode == "group":
        # a hand-edited cycle is impossible by construction; guard it anyway
        if entry.id in _seen:
            return "invalid"
        seen = _seen | {entry.id}
        if any(entry_status(runtime, entries, member, seen) == "active" for member in _members(entries, entry)):
            return "active"
        return "invalid"
    current = target_digest(runtime, entry.mode, entry.target)
    if current is None or current != entry.expected_digest:
        return "invalid"
    return "active"


# ids that no live entry references, so nothing points at them
# a removed entry is a tombstone, so its references do not protect a target
def isolated_ids(entries: Mapping[str, BookmarkEntry]) -> set[str]:
    referenced = {member for entry in entries.values() if not entry.removed for member in entry.members}
    return {bookmark_id for bookmark_id in entries if bookmark_id not in referenced}


# the member table is mutated only by --force, so guard the graph here
# a group that reaches itself would break every reader that walks members
# the recursion is small because a real member set stays in the five to nine range
def validate_acyclic(entries: Mapping[str, BookmarkEntry]) -> None:
    done: set[str] = set()
    visiting: set[str] = set()

    def visit(bookmark_id: str) -> None:
        if bookmark_id in done:
            return
        if bookmark_id in visiting:
            raise BookmarkError("bookmark.error.store.reference_cycle", {"id": bookmark_id})
        visiting.add(bookmark_id)
        entry = entries.get(bookmark_id)
        if entry is not None and entry.mode == "group":
            for member in entry.members:
                if member in entries:
                    visit(member)
        visiting.discard(bookmark_id)
        done.add(bookmark_id)

    for bookmark_id in entries:
        visit(bookmark_id)


# ==============================================================================
# private helpers
# ==============================================================================


def _members(entries: Mapping[str, BookmarkEntry], entry: BookmarkEntry) -> tuple[BookmarkEntry, ...]:
    return tuple(entries[member] for member in entry.members if member in entries)


def _ensure_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise BookmarkError("bookmark.error.store.directory_prepare_failed", {"path": str(path)}) from error


__all__ = [
    "ensure_bookmarks",
    "entry_status",
    "global_path",
    "isolated_ids",
    "load_bookmarks",
    "load_layer",
    "project_path",
    "save_bookmarks",
    "save_layer",
    "validate_acyclic",
    "write_path",
]
