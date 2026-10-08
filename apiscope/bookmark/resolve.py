# apiscope/bookmark/resolve.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from apiscope.bookmark.schema import BookmarkMode
from apiscope.cache import CacheMetadata, digest_content
from apiscope.content import ContentSnapshot, load_content
from apiscope.context import RuntimeContext
from apiscope.read_lib.registry import supports_reading
from apiscope.schema import RuntimeSource
from apiscope.source import SourceResolutionError, parse_source
from apiscope.view_lib.address import split_address
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.registry import build_tree
from apiscope.view_lib.schema import IndexedNode
from apiscope.view_lib.tree import SourceTree


# the reason a cache backed target cannot be resolved
# the reason is internal, so each command boundary maps it to its own user code
class TargetReason(StrEnum):
    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_INVALID = "source_invalid"
    CACHE_MISSING = "cache_missing"
    UNSUPPORTED = "unsupported"
    PROJECTION_FAILED = "projection_failed"
    ROUTE_NOT_FOUND = "route_not_found"
    NOT_LEAF = "not_leaf"


class TargetResolutionError(RuntimeError):
    def __init__(self, reason: TargetReason, values: Mapping[str, Any] | None = None) -> None:
        self.reason = reason
        self.values = {} if values is None else dict(values)
        super().__init__(reason.value)


@dataclass(frozen=True, slots=True)
class _LoadedTarget:
    name: str
    route: str
    source: RuntimeSource
    snapshot: ContentSnapshot
    metadata: CacheMetadata


@dataclass(frozen=True, slots=True)
class ReadTarget:
    source: RuntimeSource
    snapshot: ContentSnapshot
    metadata: CacheMetadata
    node: IndexedNode


@dataclass(frozen=True, slots=True)
class ViewTarget:
    snapshot: ContentSnapshot
    metadata: CacheMetadata
    nodes: tuple[IndexedNode, ...]


def base_directory(runtime: RuntimeContext) -> Path:
    if runtime.paths.project is not None:
        return runtime.paths.project.root
    return Path.cwd()


# one load path for every cache-backed target, shared by bookmark add and use
def _load_target(runtime: RuntimeContext, target: str) -> _LoadedTarget:
    name, route = split_address(target, runtime.config.source)
    source = runtime.config.source.get(name)
    if source is None:
        raise TargetResolutionError(TargetReason.SOURCE_NOT_FOUND, {"target": target, "name": name})

    base_dir = base_directory(runtime)
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except SourceResolutionError as error:
        raise TargetResolutionError(TargetReason.SOURCE_INVALID, {"target": target, "name": name}) from error

    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    snapshot = load_content(runtime.paths.home.cache, parsed, base_dir=base_dir, ttl_days=ttl_days)
    metadata = snapshot.metadata
    if snapshot.inspection.state in {"missing", "invalid"} or metadata is None:
        raise TargetResolutionError(TargetReason.CACHE_MISSING, {"target": target, "name": name})
    return _LoadedTarget(name=name, route=route, source=source, snapshot=snapshot, metadata=metadata)


# a read target must resolve to a leaf, so add rejects what use cannot project
def resolve_read_target(runtime: RuntimeContext, target: str) -> ReadTarget:
    loaded = _load_target(runtime, target)
    if not supports_reading(loaded.source.doc_type):
        raise TargetResolutionError(TargetReason.UNSUPPORTED, {"target": target, "name": loaded.name})
    tree = _build_tree(loaded, target)
    try:
        node = tree.resolve(loaded.route)
    except ProjectionError as error:
        raise TargetResolutionError(TargetReason.ROUTE_NOT_FOUND, {"target": target, "name": loaded.name}) from error
    if not node.is_leaf:
        raise TargetResolutionError(TargetReason.NOT_LEAF, {"target": target, "name": loaded.name})
    return ReadTarget(source=loaded.source, snapshot=loaded.snapshot, metadata=loaded.metadata, node=node)


# a view target selects a subtree, so its route must project
def resolve_view_target(runtime: RuntimeContext, target: str) -> ViewTarget:
    loaded = _load_target(runtime, target)
    tree = _build_tree(loaded, target)
    try:
        nodes = tree.select(loaded.route)
    except ProjectionError as error:
        raise TargetResolutionError(TargetReason.ROUTE_NOT_FOUND, {"target": target, "name": loaded.name}) from error
    return ViewTarget(snapshot=loaded.snapshot, metadata=loaded.metadata, nodes=nodes)


# the stored digest is the contract; a probe returns none instead of raising
def target_digest(runtime: RuntimeContext, mode: BookmarkMode, target: str) -> str | None:
    if mode == "file":
        return _file_digest(base_directory(runtime), target)
    try:
        if mode == "read":
            return resolve_read_target(runtime, target).metadata.content_digest
        return resolve_view_target(runtime, target).metadata.content_digest
    except TargetResolutionError:
        return None


def _build_tree(loaded: _LoadedTarget, target: str) -> SourceTree:
    try:
        return build_tree(loaded.source.doc_type, loaded.snapshot.content, loaded.metadata)
    except ProjectionError as error:
        raise TargetResolutionError(TargetReason.PROJECTION_FAILED, {"target": target, "name": loaded.name}) from error


def _file_digest(base_dir: Path, target: str) -> str | None:
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        return None
    return digest_content(path)


__all__ = [
    "ReadTarget",
    "TargetReason",
    "TargetResolutionError",
    "ViewTarget",
    "base_directory",
    "resolve_read_target",
    "resolve_view_target",
    "target_digest",
]
