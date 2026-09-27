# tests/read_lib/readers.unit.test.py
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml

from apiscope.cache import CacheMetadata
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.filesystem.reader import FilesystemReader
from apiscope.read_lib.llmstxt import reader as llmstxt_reader_module
from apiscope.read_lib.llmstxt.reader import LlmstxtReader
from apiscope.read_lib.openapi.reader import OpenapiReader
from apiscope.read_lib.registry import supports_reading
from apiscope.read_lib.repo.reader import RepoReader
from apiscope.read_lib.rfc.reader import RfcReader
from apiscope.read_lib.schema import ReadResult
from apiscope.schema import DocumentType
from apiscope.view_lib.schema import IndexedNode, NodeType


def test_filesystem_reader_returns_utf8_markdown(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "guide.md").write_text("guide\n", encoding="utf-8")

    result = FilesystemReader().read(content, _metadata(), _node("guide.md"))

    assert result.kind == "markdown"
    assert result.content == "guide\n"
    assert result.encoding == "utf-8"
    assert result.size == 6


def test_filesystem_reader_reports_binary_size(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "blob.bin").write_bytes(b"\x00\xff")

    result = FilesystemReader().read(content, _metadata(), _node("blob.bin"))

    assert result.kind == "binary"
    assert result.content is None
    assert result.size == 2


def test_filesystem_reader_rejects_paths_outside_content(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (tmp_path / "secret").write_text("secret", encoding="utf-8")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_invalid"):
        FilesystemReader().read(content, _metadata(), _node("../secret"))


def test_repo_reader_rejects_an_ordinary_directory_node(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "docs").mkdir(parents=True)

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_leaf"):
        RepoReader().read(content, _metadata(), _node("docs", node_type="ordinary"))


def test_openapi_reader_reads_one_operation_and_keeps_path_item_context(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        """
openapi: 3.2.1
paths:
  /pets:
    summary: Pet collection
    parameters:
      - name: limit
    get:
      $ref: '#/components/operations/ListPets'
""".lstrip(),
        encoding="utf-8",
    )

    result = OpenapiReader().read(content, _openapi_metadata(), _node("/pets/GET", key="GET"))

    assert result.target == "/pets/GET"
    assert result.kind == "text"
    assert result.content is not None
    assert yaml.safe_load(result.content) == {
        "summary": "Pet collection",
        "parameters": [{"name": "limit"}],
        "get": {"$ref": "#/components/operations/ListPets"},
    }
    assert result.media_type == "application/yaml"
    assert result.encoding == "utf-8"
    assert result.size == len(result.content.encode("utf-8"))


def test_openapi_reader_reads_a_webhook_operation(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        "openapi: 3.2.1\npaths: {}\nwebhooks:\n  orderCreated:\n    post:\n      summary: Notify the consumer\n",
        encoding="utf-8",
    )

    result = OpenapiReader().read(
        content,
        _openapi_metadata(),
        _node("webhooks/orderCreated/POST", key="POST"),
    )

    assert result.target == "webhooks/orderCreated/POST"
    assert result.content is not None
    assert yaml.safe_load(result.content) == {"post": {"summary": "Notify the consumer"}}


def test_openapi_reader_reports_a_missing_operation(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        "openapi: 3.2.1\npaths:\n  /pets:\n    get:\n      summary: List pets\n",
        encoding="utf-8",
    )

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_found"):
        OpenapiReader().read(content, _openapi_metadata(), _node("/pets/DELETE", key="DELETE"))


def test_openapi_reader_reports_a_missing_path(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text("openapi: 3.2.1\npaths: {}\n", encoding="utf-8")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_found"):
        OpenapiReader().read(content, _openapi_metadata(), _node("/missing/GET", key="GET"))


@pytest.mark.parametrize("document", ["[", "openapi: 3.2.1\npaths: []\n"])
def test_openapi_reader_rejects_invalid_documents(tmp_path: Path, document: str) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(document, encoding="utf-8")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.content_invalid"):
        OpenapiReader().read(content, _openapi_metadata(), _node("/pets/GET", key="GET"))


def test_read_result_omits_binary_body_with_the_library_template() -> None:
    result = ReadResult(target="blob.bin", kind="binary", size=7)

    assert result.render_body() == "(binary content omitted; 7 bytes)"


def test_reader_registry_supports_all_document_types() -> None:
    document_types: tuple[DocumentType, ...] = ("filesystem", "repo", "openapi", "rfc", "llmstxt")
    assert all(supports_reading(doc_type) for doc_type in document_types)


def test_rfc_reader_returns_an_xml_section(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><front><title>Example</title></front><middle><section anchor="scope">'
        "<name>Scope</name><t>Keep this paragraph.</t></section></middle></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(content, _rfc_metadata("rfc.xml"), _node("scope"))

    assert result.target == "scope"
    assert result.kind == "text"
    assert result.media_type == "application/rfc+xml"
    assert result.content == '<section anchor="scope"><name>Scope</name><t>Keep this paragraph.</t></section>'


def test_rfc_reader_returns_the_xml_overview(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        "<rfc><front><title>Example</title><abstract><t>Summary.</t></abstract></front></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(content, _rfc_metadata("rfc.xml"), _node("overview"))

    assert result.content == "<front><title>Example</title><abstract><t>Summary.</t></abstract></front>"


def test_rfc_reader_returns_one_xml_reference(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references title="Normative References"><reference anchor="RFC2119">'
        "<front><title>Key words for use in RFCs</title></front>"
        "</reference></references></back></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(
        content,
        _rfc_metadata("rfc.xml"),
        _node("references/RFC2119", key="RFC2119"),
    )

    assert result.content == (
        '<reference anchor="RFC2119"><front><title>Key words for use in RFCs</title></front></reference>'
    )


def test_rfc_reader_resolves_a_reference_group_without_a_title(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references><reference anchor="RFC2119">'
        "<front><title>Key words for use in RFCs</title></front>"
        "</reference></references></back></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(
        content,
        _rfc_metadata("rfc.xml"),
        _node("references/RFC2119", key="RFC2119"),
    )

    assert result.content is not None
    assert "<title>Key words for use in RFCs</title>" in result.content


def test_rfc_reader_returns_one_text_page(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.txt").write_text("cover\fcontents\fbody page\n", encoding="utf-8")

    result = RfcReader().read(content, _rfc_metadata("rfc.txt"), _node("page/2"))

    assert result.content == "contents"
    assert result.media_type == "text/plain"
    assert result.size == len(b"contents")


def test_llmstxt_reader_returns_the_cached_index_for_overview(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text("# Docs\n", encoding="utf-8")

    result = LlmstxtReader().read(content, _llmstxt_metadata(), _node("overview"))

    assert result.kind == "markdown"
    assert result.content == "# Docs\n"
    assert result.media_type == "text/markdown"


def test_llmstxt_reader_fetches_only_the_selected_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text("# Docs\n", encoding="utf-8")
    requests: list[str] = []
    original_client = httpx.Client

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(
            200,
            headers={"content-type": "text/markdown; charset=utf-8"},
            content=b"# Guide\n",
            request=request,
        )

    def client_factory(**kwargs: Any) -> httpx.Client:
        return original_client(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(llmstxt_reader_module.httpx, "Client", client_factory)
    url = "https://example.test/docs/guide.md"

    result = LlmstxtReader().read(
        content,
        _llmstxt_metadata(),
        _node("docs/guide.md", key="Guide", source_target=url),
    )

    assert requests == [url]
    assert result.kind == "markdown"
    assert result.content == "# Guide\n"
    assert result.as_extra("fresh")["retrieval"] == "network"
    assert sorted(path.name for path in content.iterdir()) == ["llms.txt"]


def test_llmstxt_reader_reports_http_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_client = httpx.Client

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request)

    def client_factory(**kwargs: Any) -> httpx.Client:
        return original_client(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(llmstxt_reader_module.httpx, "Client", client_factory)

    with pytest.raises(ReadError, match=r"read_lib\.reader\.read_failed"):
        LlmstxtReader().read(
            tmp_path,
            _llmstxt_metadata(),
            _node("guide.md", source_target="https://example.test/guide.md"),
        )


def test_llmstxt_reader_rejects_non_http_targets(tmp_path: Path) -> None:
    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_invalid"):
        LlmstxtReader().read(
            tmp_path,
            _llmstxt_metadata(),
            _node("guide.md", source_target="file:///tmp/guide.md"),
        )


def _node(
    path: str,
    *,
    key: str | None = None,
    node_type: NodeType = "leaf",
    source_target: str | None = None,
) -> IndexedNode:
    return IndexedNode(
        address=(1,),
        index="1",
        key=key or path,
        node_type=node_type,
        path=path,
        source_target=source_target,
    )


def _rfc_metadata(name: str) -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type="rfc",
        source="file:///rfc",
        fetched_at=datetime.now(timezone.utc),
        content_kind="file",
        content_name=name,
        content_digest="digest",
    )


def _llmstxt_metadata() -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type="llmstxt",
        source="https://example.test/llms.txt",
        fetched_at=datetime.now(timezone.utc),
        content_kind="file",
        content_name="llms.txt",
        content_digest="digest",
    )


def _openapi_metadata() -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type="openapi",
        source="file:///openapi.yaml",
        fetched_at=datetime.now(timezone.utc),
        content_kind="file",
        content_name="openapi.yaml",
        content_digest="digest",
    )


def _metadata() -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type="filesystem",
        source="file:///source",
        fetched_at=datetime.now(timezone.utc),
        content_kind="directory",
        content_name=None,
        content_digest="digest",
    )
