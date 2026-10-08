# apiscope/bookmark/resolve.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apiscope.bookmark.errors import BookmarkError
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


@dataclass(frozen=True, slots=True)
class LoadedTarget:
    name: str
    route: str
    source: RuntimeSource
    snapshot: ContentSnapshot
    metadata: CacheMetadata


@dataclass(frozen=True, slots=True)
class ReadTarget(LoadedTarget):
    tree: SourceTree
    node: IndexedNode


@dataclass(frozen=True, slots=True)
class ViewTarget(LoadedTarget):
    tree: SourceTree
    nodes: tuple[IndexedNode, ...]


def base_directory(runtime: RuntimeContext) -> Path:
    if runtime.paths.project is not None:
        return runtime.paths.project.root
    return Path.cwd()


# one load path for every cache-backed target, shared by bookmark add and use
def load_target(runtime: RuntimeContext, target: str) -> LoadedTarget:
    name, route = split_address(target, runtime.config.source)
    source = runtime.config.source.get(name)
    if source is None:
        raise BookmarkError("bookmark.error.target.source_not_found", {"target": target, "name": name})

    base_dir = base_directory(runtime)
    try:
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
    except SourceResolutionError as error:
        raise BookmarkError("bookmark.error.target.source_invalid", {"target": target}) from error

    ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
    snapshot = load_content(runtime.paths.home.cache, parsed, base_dir=base_dir, ttl_days=ttl_days)
    metadata = snapshot.metadata
    if snapshot.inspection.state in {"missing", "invalid"} or metadata is None:
        raise BookmarkError("bookmark.error.target.cache_missing", {"target": target})
    return LoadedTarget(name=name, route=route, source=source, snapshot=snapshot, metadata=metadata)


# a read target must resolve to a leaf, so add rejects what use cannot project
def resolve_read_target(runtime: RuntimeContext, target: str) -> ReadTarget:
    loaded = load_target(runtime, target)
    if not supports_reading(loaded.source.doc_type):
        raise BookmarkError("bookmark.error.target.unsupported", {"target": target})
    tree = _build_tree(loaded, target)
    try:
        node = tree.resolve(loaded.route)
    except ProjectionError as error:
        raise BookmarkError("bookmark.error.target.route_not_found", {"target": target}) from error
    if not node.is_leaf:
        raise BookmarkError("bookmark.error.target_not_leaf", {"target": target})
    return ReadTarget(
        name=loaded.name,
        route=loaded.route,
        source=loaded.source,
        snapshot=loaded.snapshot,
        metadata=loaded.metadata,
        tree=tree,
        node=node,
    )


# a view target selects a subtree, so its route must project
def resolve_view_target(runtime: RuntimeContext, target: str) -> ViewTarget:
    loaded = load_target(runtime, target)
    tree = _build_tree(loaded, target)
    try:
        nodes = tree.select(loaded.route)
    except ProjectionError as error:
        raise BookmarkError("bookmark.error.target.route_not_found", {"target": target}) from error
    return ViewTarget(
        name=loaded.name,
        route=loaded.route,
        source=loaded.source,
        snapshot=loaded.snapshot,
        metadata=loaded.metadata,
        tree=tree,
        nodes=nodes,
    )


# the stored digest is the contract; a probe returns none instead of raising
def target_digest(runtime: RuntimeContext, mode: BookmarkMode, target: str) -> str | None:
    if mode == "group":
        return ""
    if mode == "file":
        return _file_digest(base_directory(runtime), target)
    try:
        if mode == "read":
            return resolve_read_target(runtime, target).metadata.content_digest
        return resolve_view_target(runtime, target).metadata.content_digest
    except BookmarkError:
        return None


def _build_tree(loaded: LoadedTarget, target: str) -> SourceTree:
    try:
        return build_tree(loaded.source.doc_type, loaded.snapshot.content, loaded.metadata)
    except ProjectionError as error:
        raise BookmarkError("bookmark.error.target.projection_failed", {"target": target}) from error


def _file_digest(base_dir: Path, target: str) -> str | None:
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        return None
    return digest_content(path)


__all__ = [
    "LoadedTarget",
    "ReadTarget",
    "ViewTarget",
    "base_directory",
    "load_target",
    "resolve_read_target",
    "resolve_view_target",
    "target_digest",
]
