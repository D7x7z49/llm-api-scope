# apiscope/read_lib/llmstxt/reader.py
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal

from apiscope.cache import CacheMetadata
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class LlmstxtReader:
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
    ) -> ReadResult:
        if not target.is_leaf or target.path is None:
            raise ReadError(ReadReason.TARGET_NOT_LEAF, {"target": target.path or target.index})
        if target.source_target is None:
            raise ReadError(ReadReason.TARGET_NOT_FOUND, {"target": target.path})

        try:
            raw = (content / target.source_target).read_bytes()
        except OSError as error:
            raise ReadError(ReadReason.TARGET_INVALID, {"target": target.path}) from error

        media_type = mimetypes.guess_type(target.path)[0] or "application/octet-stream"
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return ReadResult(
                target=target.path,
                kind="binary",
                media_type=media_type,
                size=len(raw),
            )

        kind: Literal["text", "markdown"] = "markdown" if target.path.lower().endswith((".md", ".markdown")) else "text"
        return ReadResult(
            target=target.path,
            kind=kind,
            content=text,
            media_type=media_type,
            encoding="utf-8",
            size=len(raw),
        )
