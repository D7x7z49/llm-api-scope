# apiscope/read_lib/registry.py
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.read_lib.constants import ReadReason
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.read_lib.llmstxt.reader import LlmstxtReader
from apiscope.read_lib.openapi.reader import OpenapiReader
from apiscope.read_lib.protocols import SourceReader
from apiscope.read_lib.repo.reader import RepoReader
from apiscope.read_lib.rfc.reader import RfcReader
from apiscope.read_lib.schema import ReadResult
from apiscope.schema import DocumentType
from apiscope.view_lib.schema import IndexedNode

_READERS: dict[DocumentType, SourceReader] = {
    "filesystem": FilesystemReader(),
    "repo": RepoReader(),
    "openapi": OpenapiReader(),
    "rfc": RfcReader(),
    "llmstxt": LlmstxtReader(),
}


def supports_reading(doc_type: DocumentType) -> bool:
    return doc_type in _READERS


def read_content(
    doc_type: DocumentType,
    content: Path,
    metadata: CacheMetadata,
    target: IndexedNode,
) -> ReadResult:
    reader = _READERS.get(doc_type)
    if reader is None:
        raise ReadError(ReadReason.READER_UNSUPPORTED, {"doc_type": doc_type})
    return reader.read(content, metadata, target)


__all__ = ["read_content", "supports_reading"]
