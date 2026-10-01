# apiscope/read_lib/protocols.py
from pathlib import Path
from typing import Protocol

from apiscope.cache import CacheMetadata
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class SourceReader(Protocol):
    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult: ...
