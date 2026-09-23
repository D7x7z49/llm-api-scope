# apiscope/view_lib/repo/viewer.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.filesystem.viewer import build_filesystem_tree
from apiscope.view_lib.tree import SourceTree


class RepoViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        return build_filesystem_tree(content, metadata, exclude_git=True)
