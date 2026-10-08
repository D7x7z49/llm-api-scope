# tests/read_lib/registry.unit.test.py
from apiscope.read_lib.registry import supports_reading
from apiscope.schema import DocumentType


def test_reader_registry_supports_all_document_types() -> None:
    document_types: tuple[DocumentType, ...] = ("filesystem", "repo", "openapi", "rfc", "llmstxt", "arxiv")

    assert all(supports_reading(doc_type) for doc_type in document_types)
