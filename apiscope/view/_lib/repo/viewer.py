# apiscope/view/_lib/repo/viewer.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view._lib.filesystem.viewer import build_filesystem_tree
from apiscope.view._lib.tree import SourceTree


class RepoViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        return build_filesystem_tree(content, metadata, exclude_git=True)
