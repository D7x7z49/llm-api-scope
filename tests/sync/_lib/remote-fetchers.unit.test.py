# tests/sync/_lib/remote-fetchers.unit.test.py
import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest

from apiscope.schema import DocumentType
from apiscope.source import LlmstxtSource, OpenapiSource, RemoteLocation, RfcSource
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.llmstxt.fetcher import LlmstxtFetcher
from apiscope.sync._lib.openapi.fetcher import OpenapiFetcher
from apiscope.sync._lib.rfc.fetcher import RfcFetcher


def _remote_source(doc_type: DocumentType, url: str) -> OpenapiSource | RfcSource | LlmstxtSource:
    location = RemoteLocation(url)
    if doc_type == "openapi":
        return OpenapiSource(original=url, location=location)
    if doc_type == "rfc":
        return RfcSource(original=url, location=location)
    return LlmstxtSource(original=url, location=location)


@pytest.mark.parametrize(
    ("fetcher_type", "doc_type", "url"),
    [
        pytest.param(OpenapiFetcher, "openapi", "https://example.test/openapi.json", id="openapi"),
        pytest.param(RfcFetcher, "rfc", "https://example.test/rfc9110.txt", id="rfc"),
    ],
)
def test_remote_fetchers_store_mocked_content(
    tmp_path: Path,
    fetcher_type: type[OpenapiFetcher] | type[RfcFetcher] | type[LlmstxtFetcher],
    doc_type: DocumentType,
    url: str,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, content=b"remote content")

    install_mock_client(handler)
    source = _remote_source(doc_type, url)
    destination = tmp_path / "staging"

    result = fetcher_type().fetch(source, destination=destination)

    assert result.content_kind == "file"
    assert result.content_name == Path(url).name
    assert (destination / "content" / Path(url).name).read_bytes() == b"remote content"
    assert result.content_digest
    assert [str(request.url) for request in requests] == [url]


def test_llmstxt_fetcher_downloads_the_index_and_pages(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
    golden: Callable[[str, str], None],
) -> None:
    requests: list[str] = []
    index = b"# Docs\n\n- [Guide](guide)\n- [Intro](guide/intro.md)\n"

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        if str(request.url) == "https://example.test/docs/llms.txt":
            return httpx2.Response(200, content=index)
        return httpx2.Response(200, content=b"page content")

    install_mock_client(handler)
    url = "https://example.test/docs/llms.txt"
    source = _remote_source("llmstxt", url)
    destination = tmp_path / "staging"

    result = LlmstxtFetcher().fetch(source, destination=destination)

    index_digest = hashlib.sha256(index).hexdigest()
    page_digest = hashlib.sha256(b"page content").hexdigest()
    assert result.content_kind == "directory"
    assert result.content_name is None
    assert (destination / "content" / index_digest).read_bytes() == index
    assert (destination / "content" / page_digest).read_bytes() == b"page content"
    assert result.manifest is not None
    golden(json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", "llmstxt/manifest.json")
    assert requests == [
        url,
        "https://example.test/docs/guide",
        "https://example.test/docs/guide/intro.md",
    ]


def test_rfc_fetcher_uses_xml_when_present(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        return httpx2.Response(200, content=b"<rfc/>")

    install_mock_client(handler)
    source = _remote_source("rfc", "https://example.test/rfc9110.xml")
    destination = tmp_path / "staging"

    result = RfcFetcher().fetch(source, destination=destination)

    assert requests == ["https://example.test/rfc9110.xml"]
    assert result.content_name == "rfc9110.xml"


def test_rfc_fetcher_falls_back_to_text_when_xml_is_absent(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        if str(request.url).endswith(".xml"):
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=b"rfc text")

    install_mock_client(handler)
    source = _remote_source("rfc", "https://example.test/rfc9110.xml")
    destination = tmp_path / "staging"

    result = RfcFetcher().fetch(source, destination=destination)

    assert requests == ["https://example.test/rfc9110.xml", "https://example.test/rfc9110.txt"]
    assert result.content_name == "rfc9110.txt"


@pytest.mark.parametrize(
    ("fetcher_type", "doc_type", "url"),
    [
        pytest.param(OpenapiFetcher, "openapi", "https://example.test/openapi.json", id="openapi"),
        pytest.param(RfcFetcher, "rfc", "https://example.test/rfc9110.txt", id="rfc"),
        pytest.param(LlmstxtFetcher, "llmstxt", "https://example.test/llms.txt", id="llmstxt"),
    ],
)
def test_remote_fetchers_translate_http_errors_with_the_original_cause(
    tmp_path: Path,
    fetcher_type: type[OpenapiFetcher] | type[RfcFetcher] | type[LlmstxtFetcher],
    doc_type: DocumentType,
    url: str,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(503, request=request)

    install_mock_client(handler)
    source = _remote_source(doc_type, url)

    with pytest.raises(SourceFetchError) as raised:
        fetcher_type().fetch(source, destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.transport_failed"
    assert isinstance(raised.value.__cause__, httpx2.HTTPStatusError)
