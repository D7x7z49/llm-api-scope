# tests/sync/_lib/openapi/openapi-parser.unit.test.py
from pathlib import Path

from apiscope.sync._lib.openapi.parser import OpenapiParser
from apiscope.sync._lib.schema import RemoteSource


def test_openapi_parser_keeps_a_remote_document_location(tmp_path: Path) -> None:
    parsed = OpenapiParser().parse("https://example.test/openapi.json", base_dir=tmp_path)

    assert parsed.doc_type == "openapi"
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.canonical == "https://example.test/openapi.json"
