# apiscope/openapi/reader.py

import json
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import yaml


class HttpMethod(StrEnum):
    GET = "get"
    PUT = "put"
    POST = "post"
    DELETE = "delete"
    OPTIONS = "options"
    HEAD = "head"
    PATCH = "patch"
    TRACE = "trace"


class OpenapiReader:
    _payload: dict[str, Any]

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    @classmethod
    def load(cls, path: Path) -> "OpenapiReader":
        text = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            payload = yaml.safe_load(text)
        else:
            payload = json.loads(text)
        return cls(payload)

    @property
    def paths(self) -> dict[str, dict[str, Any]]:
        return cast(dict[str, dict[str, Any]], self._payload.get("paths", {}))

    def filter_paths(self, *methods: HttpMethod) -> dict[str, dict[str, Any]]:
        method_set = set(methods)
        result: dict[str, dict[str, Any]] = {}
        for path_name, path_item in self.paths.items():
            filtered: dict[str, Any] = {k: v for k, v in path_item.items() if k in method_set}
            if filtered:
                result[path_name] = filtered
        return result

    def get_operation(self, path: str, method: HttpMethod) -> dict[str, Any]:
        path_item: dict[str, Any] = self._payload.get("paths", {}).get(path, {})
        return cast(dict[str, Any], path_item.get(method, {}))

    def resolve_ref(self, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for k, v in data.items():
            if k == "$ref" and isinstance(v, str):
                resolved = self._deref(v)
                if resolved is not None:
                    return self.resolve_ref(resolved)
                result[k] = v
            elif isinstance(v, dict):
                result[k] = self.resolve_ref(v)
            elif isinstance(v, list):
                result[k] = [
                    self.resolve_ref(item) if isinstance(item, dict) else item for item in v
                ]
            else:
                result[k] = v
        return result

    def _deref(self, ref: str) -> dict[str, Any] | None:
        if not ref.startswith("#/"):
            return None
        parts = ref.removeprefix("#/").split("/")
        target: Any = self._payload
        for part in parts:
            if not isinstance(target, dict) or part not in target:
                return None
            target = target[part]
        return target if isinstance(target, dict) else None
