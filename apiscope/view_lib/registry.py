# apiscope/view_lib/registry.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.schema import DocumentType
from apiscope.view_lib.arxiv.viewer import ArxivViewer
from apiscope.view_lib.filesystem.viewer import FilesystemViewer
from apiscope.view_lib.llmstxt.viewer import LlmstxtViewer
from apiscope.view_lib.openapi.viewer import OpenapiViewer
from apiscope.view_lib.protocols import SourceViewer
from apiscope.view_lib.repo.viewer import RepoViewer
from apiscope.view_lib.rfc.viewer import RfcViewer
from apiscope.view_lib.tree import SourceTree

_VIEWERS: dict[DocumentType, SourceViewer] = {
    "filesystem": FilesystemViewer(),
    "repo": RepoViewer(),
    "openapi": OpenapiViewer(),
    "rfc": RfcViewer(),
    "llmstxt": LlmstxtViewer(),
    "arxiv": ArxivViewer(),
}


def build_tree(doc_type: DocumentType, content: Path, metadata: CacheMetadata) -> SourceTree:
    return _VIEWERS[doc_type].build(content, metadata)


__all__ = ["build_tree"]
