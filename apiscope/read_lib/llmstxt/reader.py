# apiscope/read_lib/llmstxt/reader.py
from __future__ import annotations

from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class LlmstxtReader:
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult:
        del proxy
        return FilesystemReader().read(content, metadata, target)
