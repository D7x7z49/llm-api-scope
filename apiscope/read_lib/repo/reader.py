# apiscope/read_lib/repo/reader.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.read_lib.schema import ReadResult
from apiscope.view_lib.schema import IndexedNode


class RepoReader:
    def __init__(self) -> None:
        self._reader = FilesystemReader()

    def read(
        self,
        content: Path,
        metadata: CacheMetadata,
        target: IndexedNode,
        *,
        proxy: str | None = None,
    ) -> ReadResult:
        return self._reader.read(content, metadata, target, proxy=proxy)
