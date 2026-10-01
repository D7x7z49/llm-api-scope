# apiscope/view_lib/llmstxt/viewer.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.filesystem.viewer import build_filesystem_tree
from apiscope.view_lib.tree import SourceTree


class LlmstxtViewer:
    def build(self, content: Path, metadata: CacheMetadata) -> SourceTree:
        return build_filesystem_tree(content, metadata, exclude_git=False)
