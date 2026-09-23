# apiscope/view_lib/protocols.py
from pathlib import Path
from typing import Protocol

from apiscope.cache import CacheMetadata
from apiscope.view_lib.tree import SourceTree


class SourceViewer(Protocol):
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree: ...
