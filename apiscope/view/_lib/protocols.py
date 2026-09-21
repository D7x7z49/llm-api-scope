# apiscope/view/_lib/protocols.py
from pathlib import Path
from typing import Protocol

from apiscope.cache import CacheMetadata
from apiscope.view._lib.tree import SourceTree


class SourceViewer(Protocol):
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree: ...
