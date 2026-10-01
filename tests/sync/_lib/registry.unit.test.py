# tests/sync/_lib/registry.unit.test.py
from pathlib import Path

import pytest

from apiscope.source import SourceParseReason, SourceResolutionError
from apiscope.source import parse_source as resolve_source
from apiscope.sync._lib.errors import SourceParseError
from apiscope.sync._lib.registry import parse_source
from apiscope.sync.constants import MESSAGE_TEMPLATES


def test_sync_has_a_message_template_for_each_shared_source_error() -> None:
    assert {f"sync.error.{reason.value}" for reason in SourceParseReason} <= set(MESSAGE_TEMPLATES)


def test_sync_parser_preserves_the_shared_source_identity(tmp_path: Path) -> None:
    source = "HTTPS://Example.TEST/openapi.json"

    shared = resolve_source("openapi", source, base_dir=tmp_path)
    adapted = parse_source("openapi", source, base_dir=tmp_path)

    assert adapted == shared
    assert adapted.canonical == "https://example.test/openapi.json"


def test_sync_parser_adapts_a_shared_parse_error(tmp_path: Path) -> None:
    with pytest.raises(SourceParseError) as raised:
        parse_source("openapi", "ftp://example.test/openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.unsupported_scheme"
    assert raised.value.values == {"scheme": "ftp"}
    assert isinstance(raised.value.__cause__, SourceResolutionError)
