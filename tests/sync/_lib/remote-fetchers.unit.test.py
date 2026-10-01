# tests/sync/_lib/remote-fetchers.unit.test.py
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from apiscope.schema import DocumentType
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.llmstxt.fetcher import LlmstxtFetcher
from apiscope.sync._lib.openapi.fetcher import OpenapiFetcher
from apiscope.sync._lib.rfc.fetcher import RfcFetcher
from apiscope.sync._lib.schema import ParsedSource, RemoteSource


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
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=b"remote content")

    install_httpx_mock_client(handler)
    source = ParsedSource(
        doc_type=doc_type,
        original=url,
        canonical=url,
        location=RemoteSource(url),
    )
    destination = tmp_path / "staging"

    result = fetcher_type().fetch(source, destination=destination)

    assert result.content_kind == "file"
    assert result.content_name == Path(url).name
    assert (destination / "content" / Path(url).name).read_bytes() == b"remote content"
    assert result.content_digest
    assert [str(request.url) for request in requests] == [url]


def test_llmstxt_fetcher_downloads_the_index_and_pages(
    tmp_path: Path,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    requests: list[str] = []
    index = b"# Docs\n\n- [Guide](guide/intro.md): the guide\n"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if str(request.url) == "https://example.test/docs/llms.txt":
            return httpx.Response(200, content=index)
        return httpx.Response(200, content=b"page content")

    install_httpx_mock_client(handler)
    url = "https://example.test/docs/llms.txt"
    source = ParsedSource(doc_type="llmstxt", original=url, canonical=url, location=RemoteSource(url))
    destination = tmp_path / "staging"

    result = LlmstxtFetcher().fetch(source, destination=destination)

    assert result.content_kind == "directory"
    assert result.content_name is None
    assert (destination / "content" / "llms.txt").read_bytes() == index
    assert (destination / "content" / "guide" / "intro.md").read_bytes() == b"page content"
    assert requests == [url, "https://example.test/docs/guide/intro.md"]


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
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request)

    install_httpx_mock_client(handler)
    source = ParsedSource(
        doc_type=doc_type,
        original=url,
        canonical=url,
        location=RemoteSource(url),
    )

    with pytest.raises(SourceFetchError) as raised:
        fetcher_type().fetch(source, destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.transport_failed"
    assert isinstance(raised.value.__cause__, httpx.HTTPStatusError)
