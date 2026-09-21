# tests/sync/_lib/filesystem/filesystem-parser.unit.test.py
from pathlib import Path

import pytest

from apiscope.sync._lib.errors import SourceParseError
from apiscope.sync._lib.filesystem.parser import FilesystemParser
from apiscope.sync._lib.schema import LocalSource


def test_filesystem_parser_resolves_a_relative_path(tmp_path: Path) -> None:
    parsed = FilesystemParser().parse("./docs", base_dir=tmp_path)

    assert parsed.doc_type == "filesystem"
    assert parsed.canonical == (tmp_path / "docs").resolve().as_posix()
    assert isinstance(parsed.location, LocalSource)
    assert parsed.location.path == (tmp_path / "docs").resolve()


def test_filesystem_parser_reports_a_remote_source_error(tmp_path: Path) -> None:
    with pytest.raises(SourceParseError) as raised:
        FilesystemParser().parse("https://example.test/docs", base_dir=tmp_path)

    assert raised.value.reason_code == "parse.filesystem_path_required"
    assert raised.value.values == {}
