# tests/sync/_lib/rfc/rfc-parser.unit.test.py
from pathlib import Path

from apiscope.sync._lib.rfc.parser import RfcParser
from apiscope.sync._lib.schema import RemoteSource


def test_rfc_parser_accepts_an_http_document_location(tmp_path: Path) -> None:
    parsed = RfcParser().parse("https://www.rfc-editor.org/rfc/rfc9110.txt", base_dir=tmp_path)

    assert parsed.doc_type == "rfc"
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.canonical.endswith("/rfc9110.txt")
