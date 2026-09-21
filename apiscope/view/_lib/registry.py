# apiscope/view/_lib/registry.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.schema import DocumentType
from apiscope.view._lib.filesystem.viewer import FilesystemViewer
from apiscope.view._lib.llmstxt.viewer import LlmstxtViewer
from apiscope.view._lib.openapi.viewer import OpenapiViewer
from apiscope.view._lib.protocols import SourceViewer
from apiscope.view._lib.repo.viewer import RepoViewer
from apiscope.view._lib.rfc.viewer import RfcViewer
from apiscope.view._lib.source import ViewSource, parse_source
from apiscope.view._lib.tree import SourceTree

_VIEWERS: dict[DocumentType, SourceViewer] = {
    "filesystem": FilesystemViewer(),
    "repo": RepoViewer(),
    "openapi": OpenapiViewer(),
    "rfc": RfcViewer(),
    "llmstxt": LlmstxtViewer(),
}


def build_view(doc_type: DocumentType, content: Path, metadata: CacheMetadata) -> SourceTree:
    return _VIEWERS[doc_type].build(content, metadata)


__all__ = ["ViewSource", "build_view", "parse_source"]
