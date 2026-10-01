# tests/source.unit.test.py
from pathlib import Path

import pytest

from apiscope.schema import DocumentType
from apiscope.source import LocalSource, RemoteSource, SourceResolutionError, parse_source


@pytest.mark.parametrize(
    ("doc_type", "source", "canonical"),
    [
        ("repo", "file://example.test/docs.git", "file://example.test/docs.git"),
        ("repo", "git://example.test/docs.git", "git://example.test/docs.git"),
        ("repo", "ssh://example.test/docs.git", "ssh://example.test/docs.git"),
        ("repo", "HTTPS://Example.TEST/docs.git", "https://example.test/docs.git"),
        ("openapi", "http://example.test/openapi.json", "http://example.test/openapi.json"),
        ("rfc", "https://example.test/rfc.txt", "https://example.test/rfc.txt"),
        ("llmstxt", "https://example.test/llms.txt", "https://example.test/llms.txt"),
    ],
)
def test_parse_source_accepts_supported_remote_locations(
    tmp_path: Path,
    doc_type: DocumentType,
    source: str,
    canonical: str,
) -> None:
    parsed = parse_source(doc_type, source, base_dir=tmp_path)

    assert parsed.canonical == canonical
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.location.url == canonical


@pytest.mark.parametrize("doc_type", ["filesystem", "repo", "openapi", "rfc", "llmstxt"])
def test_parse_source_resolves_a_local_path(tmp_path: Path, doc_type: DocumentType) -> None:
    parsed = parse_source(doc_type, "./specs/api.yaml", base_dir=tmp_path)

    assert parsed.canonical == (tmp_path / "specs" / "api.yaml").resolve().as_posix()
    assert isinstance(parsed.location, LocalSource)
    assert parsed.location.path == (tmp_path / "specs" / "api.yaml").resolve()


@pytest.mark.parametrize(
    ("doc_type", "source"),
    [
        ("openapi", "ftp://example.test/openapi.json"),
        ("rfc", "git://example.test/rfc.xml"),
        ("llmstxt", "ssh://example.test/llms.txt"),
        ("filesystem", "https://example.test/docs"),
    ],
)
def test_parse_source_rejects_unsupported_schemes(
    tmp_path: Path,
    doc_type: DocumentType,
    source: str,
) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source(doc_type, source, base_dir=tmp_path)

    expected = (
        "source.parse.filesystem_path_required" if doc_type == "filesystem" else "source.parse.unsupported_scheme"
    )
    assert raised.value.reason_code == expected


def test_parse_source_rejects_an_empty_source(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", "  ", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.source_empty"


def test_parse_source_rejects_a_remote_location_without_a_host(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https:///openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.remote_host_missing"


def test_parse_source_rejects_remote_credentials(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https://user:secret@example.test/openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.credentials_unsupported"


def test_parse_source_rejects_remote_fragments(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https://example.test/openapi.json#schema", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.fragments_unsupported"


def test_parse_source_wraps_an_invalid_port(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https://example.test:invalid/openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.location_invalid"
    assert "detail" in raised.value.values


def test_parse_source_preserves_brackets_in_an_ipv6_authority(tmp_path: Path) -> None:
    parsed = parse_source("openapi", "HTTPS://[2001:DB8::1]:8443/openapi.json", base_dir=tmp_path)

    assert parsed.canonical == "https://[2001:db8::1]:8443/openapi.json"
    assert isinstance(parsed.location, RemoteSource)
    assert parsed.location.url == parsed.canonical


def test_parse_source_wraps_an_invalid_remote_authority(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https://[invalid/openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.location_invalid"


def test_parse_source_wraps_an_invalid_filesystem_path(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", "\x00", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.filesystem_path_invalid"
