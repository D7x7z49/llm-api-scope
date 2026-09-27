# apiscope/read_lib/openapi/reader.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from apiscope.cache import CacheMetadata
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.openapi.constants import STANDARD_METHODS
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class OpenapiReader:
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult:
        if not target.is_leaf or target.path is None or target.key is None:
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path or target.index})
        method = target.key
        item_target = _path_item_for_operation(target.path, method)
        collection_name, item_name = _path_item_target(item_target)
        document = _load_document(_content_file(content, metadata))
        if collection_name not in document:
            raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})
        path_items = document[collection_name]
        if not isinstance(path_items, Mapping):
            raise ReadError(ReadReason.CONTENT_INVALID)
        if item_name not in path_items:
            raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})

        path_item = path_items[item_name]
        if not isinstance(path_item, Mapping):
            raise ReadError(ReadReason.CONTENT_INVALID)
        selected_item = _select_operation(path_item, method, target.path)

        text = yaml.safe_dump(dict(selected_item), allow_unicode=True, sort_keys=False)
        return ReadResult(
            target=target.path,
            kind="text",
            content=text,
            media_type="application/yaml",
            encoding="utf-8",
            size=len(text.encode("utf-8")),
        )


def _path_item_for_operation(path: str, method: str) -> str:
    suffix = f"/{method}"
    if not path.endswith(suffix):
        raise ReadError(ReadReason.TARGET_INVALID, {"target": path})
    return path[: -len(suffix)] or "/"


def _path_item_target(target: str) -> tuple[str, str]:
    if target == "webhooks" or target.startswith("webhooks/"):
        return "webhooks", target.removeprefix("webhooks").lstrip("/")
    path = target if target.startswith("/") else f"/{target}"
    return "paths", path


def _select_operation(path_item: Mapping[str, Any], method: str, target: str) -> Mapping[str, Any]:
    method_key = method.lower()
    is_standard_method = method_key in STANDARD_METHODS
    if is_standard_method:
        operation = path_item.get(method_key)
        selected_key = method_key
    else:
        additional_operations = path_item.get("additionalOperations")
        operation = additional_operations.get(method) if isinstance(additional_operations, Mapping) else None
        selected_key = method

    if not isinstance(operation, Mapping):
        raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target})

    selected_item: dict[str, Any] = {}
    for key, value in path_item.items():
        if isinstance(key, str) and key.lower() in STANDARD_METHODS:
            if is_standard_method and key.lower() == selected_key:
                selected_item[key] = value
        elif key == "additionalOperations":
            if not is_standard_method:
                selected_item[key] = {selected_key: operation}
        else:
            selected_item[key] = value
    return selected_item


def _content_file(content: Path, metadata: CacheMetadata) -> Path:
    if metadata.content_kind != "file" or metadata.content_name is None:
        raise ReadError(ReadReason.CONTENT_INVALID)
    try:
        root = content.resolve(strict=True)
        path = (root / metadata.content_name).resolve(strict=True)
        path.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        raise ReadError(ReadReason.CONTENT_INVALID) from error
    if not path.is_file():
        raise ReadError(ReadReason.CONTENT_INVALID)
    return path


def _load_document(path: Path) -> Mapping[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ReadError(ReadReason.CONTENT_INVALID) from error
    if not isinstance(document, Mapping):
        raise ReadError(ReadReason.CONTENT_INVALID)
    return document
