# tests/sync/_lib/llmstxt/llmstxt-parser.unit.test.py
from pathlib import Path

from apiscope.sync._lib.llmstxt.parser import LlmstxtParser
from apiscope.sync._lib.schema import RemoteSource


def test_llmstxt_parser_accepts_an_https_document_location(tmp_path: Path) -> None:
    parsed = LlmstxtParser().parse("https://example.test/llms.txt", base_dir=tmp_path)

    assert parsed.doc_type == "llmstxt"
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.canonical == "https://example.test/llms.txt"
