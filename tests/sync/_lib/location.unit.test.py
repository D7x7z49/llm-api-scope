# tests/sync/_lib/location.unit.test.py
from pathlib import Path

import pytest

from apiscope.sync._lib.errors import SourceLocationError
from apiscope.sync._lib.location import parse_local_or_remote
from apiscope.sync._lib.schema import RemoteSource


def test_location_parser_reports_structured_credentials_error(tmp_path: Path) -> None:
    with pytest.raises(SourceLocationError) as raised:
        parse_local_or_remote(
            "https://user:secret@example.test/docs",
            base_dir=tmp_path,
            remote_schemes=frozenset({"http", "https"}),
        )

    assert raised.value.reason_code == "parse.credentials_unsupported"
    assert raised.value.values == {}


def test_location_parser_returns_a_canonical_remote_source(tmp_path: Path) -> None:
    canonical, location = parse_local_or_remote(
        "HTTPS://Example.TEST/docs",
        base_dir=tmp_path,
        remote_schemes=frozenset({"http", "https"}),
    )

    assert canonical == "https://example.test/docs"
    assert isinstance(location, RemoteSource)
