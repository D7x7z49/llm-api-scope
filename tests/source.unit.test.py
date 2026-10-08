# tests/source.unit.test.py
from pathlib import Path, PureWindowsPath

import pytest

from apiscope.schema import DocumentType
from apiscope.source import (
    ArxivSource,
    LocalLocation,
    RemoteLocation,
    RepoSource,
    RfcSource,
    SourceResolutionError,
    cache_identity,
    parse_source,
)


@pytest.mark.parametrize(
    ("doc_type", "source", "transport_url"),
    [
        ("repo", "HTTPS://Example.TEST/docs.git", "https://example.test/docs.git"),
        ("openapi", "http://example.test/openapi.json", "http://example.test/openapi.json"),
        ("llmstxt", "https://example.test/llms.txt", "https://example.test/llms.txt"),
    ],
)
def test_parse_source_accepts_supported_remote_locations(
    tmp_path: Path,
    doc_type: DocumentType,
    source: str,
    transport_url: str,
) -> None:
    parsed = parse_source(doc_type, source, base_dir=tmp_path)

    assert parsed.original == source
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == transport_url


@pytest.mark.parametrize("doc_type", ["filesystem", "repo", "openapi"])
def test_parse_source_resolves_a_local_path(tmp_path: Path, doc_type: DocumentType) -> None:
    parsed = parse_source(doc_type, "./specs/api.yaml", base_dir=tmp_path)

    assert cache_identity(parsed, base_dir=tmp_path) == f"{tmp_path.as_posix()}\0./specs/api.yaml"
    assert isinstance(parsed.location, LocalLocation)
    assert parsed.location.path == (tmp_path / "specs" / "api.yaml").resolve()


@pytest.mark.parametrize("doc_type", ["filesystem", "repo", "openapi"])
def test_parse_source_treats_a_windows_drive_path_as_local(tmp_path: Path, doc_type: DocumentType) -> None:
    source = PureWindowsPath("C:/work/docs").as_posix()

    parsed = parse_source(doc_type, source, base_dir=tmp_path)

    assert isinstance(parsed.location, LocalLocation)


@pytest.mark.parametrize(
    ("doc_type", "source", "expected"),
    [
        ("openapi", "ftp://example.test/openapi.json", "source.parse.unsupported_scheme"),
        ("repo", "git://example.test/docs.git", "source.parse.unsupported_scheme"),
        ("llmstxt", "ssh://example.test/llms.txt", "source.parse.unsupported_scheme"),
        ("filesystem", "https://example.test/docs", "source.parse.filesystem_path_required"),
    ],
)
def test_parse_source_rejects_unsupported_schemes(
    tmp_path: Path,
    doc_type: DocumentType,
    source: str,
    expected: str,
) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source(doc_type, source, base_dir=tmp_path)

    assert raised.value.reason_code == expected


def test_parse_rfc_source_keeps_the_number(tmp_path: Path) -> None:
    parsed = parse_source("rfc", "9110", base_dir=tmp_path)

    assert isinstance(parsed, RfcSource)
    assert parsed.original == "9110"
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == "https://www.rfc-editor.org/rfc/rfc9110.xml"


@pytest.mark.parametrize(
    "source",
    ["0", "-1", "rfc9110", "9110.txt", "./rfc.txt", "https://example.test/rfc.txt", "\u00b2", "\uff11\uff12"],
)
def test_parse_rfc_source_rejects_a_non_number(tmp_path: Path, source: str) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("rfc", source, base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.rfc_number_invalid"


def test_parse_rfc_source_wraps_an_integer_conversion_limit(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("rfc", "9" * 5000, base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.rfc_number_invalid"


@pytest.mark.parametrize(
    "source",
    [
        "0704.0001",
        "1412.9999",
        "1501.00001",
        "1706.03762v7",
        "hep-th/9901001",
        "math.GT/0309136v1",
        "astro-ph/9107001",
    ],
)
def test_parse_arxiv_accepts_canonical_identifiers(tmp_path: Path, source: str) -> None:
    parsed = parse_source("arxiv", source, base_dir=tmp_path)

    assert isinstance(parsed, ArxivSource)
    assert parsed.original == source
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == f"https://arxiv.org/html/{source}"
    assert cache_identity(parsed, base_dir=tmp_path) == source


@pytest.mark.parametrize(
    "source",
    [
        "0703.0001",
        "0704.00001",
        "1412.00001",
        "1501.0001",
        "1313.0001",
        "1501.00000",
        "1706.03762v0",
        "1706.03762v01",
        "hep-th/9106001",
        "hep-th/0704001",
        "hep-th/9913001",
        "math.Gt/0309136",
        "arXiv:1706.03762",
        "https://arxiv.org/abs/1706.03762",
        "\u0661\u0667\u0660\u0666.\u0660\u0660\u0660\u0661",
    ],
)
def test_parse_arxiv_rejects_noncanonical_identifiers(tmp_path: Path, source: str) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("arxiv", source, base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.arxiv_identifier_invalid"


def test_parse_llmstxt_source_rejects_a_local_path(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("llmstxt", "./llms.txt", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.local_form_unsupported"


def test_parse_source_rejects_an_empty_source(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", "", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.source_empty"


def test_parse_source_rejects_surrounding_whitespace(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", " ./docs ", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.source_whitespace"


def test_parse_source_rejects_a_home_relative_path(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", "~/docs", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.path_home_unsupported"


def test_parse_repo_source_rejects_a_subpath_with_surrounding_slashes(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("repo", "https://github.com/example/api.git/docs/", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.subpath_invalid"


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

    assert parsed.original == "HTTPS://[2001:DB8::1]:8443/openapi.json"
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == "https://[2001:db8::1]:8443/openapi.json"


def test_parse_source_wraps_an_invalid_remote_authority(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("openapi", "https://[invalid/openapi.json", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.location_invalid"


def test_parse_source_wraps_an_invalid_filesystem_path(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("filesystem", "\x00", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.filesystem_path_invalid"


def test_parse_repo_source_keeps_a_subpath_and_a_ref(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://github.com/example/api.git/docs@main", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == "https://github.com/example/api.git"
    assert parsed.original == "https://github.com/example/api.git/docs@main"
    assert parsed.subpath == "docs"
    assert parsed.ref == "main"


def test_parse_repo_source_keeps_a_ref_only(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://github.com/example/api.git@v1.0.0", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert parsed.subpath is None
    assert parsed.ref == "v1.0.0"
    assert parsed.original == "https://github.com/example/api.git@v1.0.0"


def test_parse_repo_source_keeps_a_subpath_only(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://github.com/example/api.git/docs", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert parsed.subpath == "docs"
    assert parsed.ref is None
    assert parsed.original == "https://github.com/example/api.git/docs"


def test_parse_repo_source_does_not_split_a_git_marker_in_the_host(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://example.git/docs", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert isinstance(parsed.location, RemoteLocation)
    assert parsed.location.url == "https://example.git/docs"
    assert parsed.subpath is None
    assert parsed.original == "https://example.git/docs"


def test_parse_repo_source_rejects_an_scp_location(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("repo", "git@github.com:octocat/Hello-World.git@master", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.scp_unsupported"


def test_parse_repo_source_keeps_an_encoded_at_in_the_ref(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://github.com/example/api.git@feature%40x", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert parsed.ref == "feature%40x"


def test_parse_repo_source_resolves_a_local_subpath(tmp_path: Path) -> None:
    parsed = parse_source("repo", "./repo.git/docs@main", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert isinstance(parsed.location, LocalLocation)
    assert parsed.location.path == (tmp_path / "repo.git").resolve()
    assert parsed.subpath == "docs"
    assert parsed.ref == "main"


def test_parse_repo_source_finds_a_local_repo_root(tmp_path: Path) -> None:
    (tmp_path / "repo" / ".git").mkdir(parents=True)

    parsed = parse_source("repo", "./repo/docs@main", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert isinstance(parsed.location, LocalLocation)
    assert parsed.location.path == (tmp_path / "repo").resolve()
    assert parsed.subpath == "docs"
    assert parsed.ref == "main"


def test_parse_repo_source_rejects_an_empty_ref(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("repo", "https://github.com/example/api.git@", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.ref_invalid"


def test_parse_repo_source_keeps_a_short_hash_ref(tmp_path: Path) -> None:
    parsed = parse_source("repo", "https://github.com/example/api.git@1a2b3c4", base_dir=tmp_path)

    assert isinstance(parsed, RepoSource)
    assert parsed.ref == "1a2b3c4"


def test_parse_repo_source_rejects_an_option_like_ref(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("repo", "https://github.com/example/api.git@--upload-pack", base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.ref_invalid"


@pytest.mark.parametrize(
    "source",
    [
        "https://github.com/example/api.git/../etc@main",
        "https://github.com/example/api.git/..@main",
        "https://github.com/example/api.git/.@main",
    ],
)
def test_parse_repo_source_rejects_an_unsafe_subpath(tmp_path: Path, source: str) -> None:
    with pytest.raises(SourceResolutionError) as raised:
        parse_source("repo", source, base_dir=tmp_path)

    assert raised.value.reason_code == "source.parse.subpath_invalid"


def test_parse_source_keeps_distinct_remote_spellings(tmp_path: Path) -> None:
    first = parse_source("openapi", "HTTPS://Example.TEST/openapi.json", base_dir=tmp_path)
    second = parse_source("openapi", "https://example.test/openapi.json", base_dir=tmp_path)

    assert cache_identity(first, base_dir=tmp_path) == "HTTPS://Example.TEST/openapi.json"
    assert cache_identity(second, base_dir=tmp_path) == "https://example.test/openapi.json"
    assert cache_identity(first, base_dir=tmp_path) != cache_identity(second, base_dir=tmp_path)


def test_cache_identity_keeps_distinct_local_spellings(tmp_path: Path) -> None:
    first = parse_source("filesystem", "docs/api.yaml", base_dir=tmp_path)
    second = parse_source("filesystem", "./docs/api.yaml", base_dir=tmp_path)

    assert cache_identity(first, base_dir=tmp_path) != cache_identity(second, base_dir=tmp_path)


def test_cache_identity_scopes_a_relative_path_to_its_project(tmp_path: Path) -> None:
    other = tmp_path / "other"
    parsed = parse_source("filesystem", "docs/api.yaml", base_dir=tmp_path)

    assert cache_identity(parsed, base_dir=tmp_path) != cache_identity(parsed, base_dir=other)
