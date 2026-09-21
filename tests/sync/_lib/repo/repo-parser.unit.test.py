# tests/sync/_lib/repo/repo-parser.unit.test.py
from pathlib import Path

from apiscope.sync._lib.repo.parser import RepoParser
from apiscope.sync._lib.schema import RemoteSource


def test_repo_parser_canonicalizes_a_remote_host(tmp_path: Path) -> None:
    parsed = RepoParser().parse("HTTPS://Example.TEST/docs.git", base_dir=tmp_path)

    assert parsed.doc_type == "repo"
    assert parsed.canonical == "https://example.test/docs.git"
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.location.url == parsed.canonical
