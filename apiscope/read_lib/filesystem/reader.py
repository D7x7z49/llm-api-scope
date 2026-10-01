# apiscope/read_lib/filesystem/reader.py
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal

from apiscope.cache import CacheMetadata
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class FilesystemReader:
    def read(
        self,
        content: Path,
        _metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult:
        if not target.is_leaf or target.path is None:
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path or target.index})
        path = _resolve_target(content, target.path)
        if path.is_dir():
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path})
        if path.is_file():
            return _read_file(path, target.path)
        raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})


def _resolve_target(content: Path, target: str) -> Path:
    try:
        root = content.resolve(strict=True)
        resolved = (root / Path(target)).resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except (OSError, RuntimeError, ValueError) as error:
        raise ReadError(ReadReason.TARGET_INVALID, {"target": target}) from error


def _read_file(path: Path, target: str) -> ReadResult:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ReadError(ReadReason.READ_FAILED, {"target": target}) from error

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ReadResult(
            target=target,
            kind="binary",
            media_type=media_type,
            size=len(raw),
        )

    kind: Literal["text", "markdown"] = "markdown" if path.suffix.lower() in {".md", ".markdown"} else "text"
    return ReadResult(
        target=target,
        kind=kind,
        content=text,
        media_type=media_type,
        encoding="utf-8",
        size=len(raw),
    )
