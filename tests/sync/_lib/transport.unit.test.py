# tests/sync/_lib/transport.unit.test.py
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from apiscope.cache import digest_content
from apiscope.sync._lib import transport
from apiscope.sync._lib.schema import RemoteLocation


def test_fetch_location_writes_redirected_remote_content(
    tmp_path: Path,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/spec.json":
            return httpx.Response(302, headers={"Location": "/final.json"})
        return httpx.Response(200, content=b'{"openapi":"3.1.0"}')

    install_httpx_mock_client(handler)
    destination = tmp_path / "staging"

    content_kind, content_name, content_digest = transport.fetch_location(
        RemoteLocation("https://example.test/spec.json"),
        destination=destination,
    )

    content_path = destination / "content" / "spec.json"
    assert content_kind == "file"
    assert content_name == "spec.json"
    assert content_path.read_bytes() == b'{"openapi":"3.1.0"}'
    assert content_digest == digest_content(destination / "content")
    assert [request.url.path for request in requests] == ["/spec.json", "/final.json"]


def test_fetch_location_passes_a_proxy_to_httpx(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: dict[str, Any] = {}

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
            del exception_type, exception, traceback

        def get(self, url: str) -> httpx.Response:
            return httpx.Response(200, request=httpx.Request("GET", url), content=b"rfc")

    def client_factory(**kwargs: Any) -> FakeClient:
        options.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(transport.httpx, "Client", client_factory)

    transport.fetch_location(
        RemoteLocation("https://example.test/rfc.txt"),
        destination=tmp_path / "staging",
        proxy="http://proxy.example.test:8080",
    )

    assert options == {
        "follow_redirects": True,
        "timeout": transport.HTTP_TIMEOUT_SECONDS,
        "proxy": "http://proxy.example.test:8080",
        "trust_env": False,
    }


def test_fetch_location_bypasses_the_proxy_for_a_no_proxy_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: dict[str, Any] = {}

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
            del exception_type, exception, traceback

        def get(self, url: str) -> httpx.Response:
            return httpx.Response(200, request=httpx.Request("GET", url), content=b"direct")

    def client_factory(**kwargs: Any) -> FakeClient:
        options.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(transport.httpx, "Client", client_factory)

    transport.fetch_location(
        RemoteLocation("https://api.example.test/rfc.txt"),
        destination=tmp_path / "staging",
        proxy="http://proxy.example.test:8080",
        no_proxy="example.test",
    )

    assert "proxy" not in options
    assert options["trust_env"] is False


def test_fetch_location_ignores_proxy_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
    httpx_client_options: dict[str, Any],
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://environment.example.test:8080")
    monkeypatch.setenv("NO_PROXY", "example.test")
    install_httpx_mock_client(lambda request: httpx.Response(200, request=request, content=b"direct"))

    transport.fetch_location(
        RemoteLocation("https://example.test/document"),
        destination=tmp_path / "staging",
    )

    assert httpx_client_options == {
        "follow_redirects": True,
        "timeout": transport.HTTP_TIMEOUT_SECONDS,
        "trust_env": False,
    }


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(httpx.Response(404, content=b"missing"), id="status-error"),
        pytest.param(httpx.Response(503, content=b"unavailable"), id="server-error"),
    ],
)
def test_fetch_location_propagates_http_status_errors(
    tmp_path: Path,
    response: httpx.Response,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    install_httpx_mock_client(lambda request: response)

    with pytest.raises(httpx.HTTPStatusError):
        transport.fetch_location(
            RemoteLocation("https://example.test/document"),
            destination=tmp_path / "staging",
        )


def test_fetch_location_propagates_http_transport_errors(
    tmp_path: Path,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    install_httpx_mock_client(handler)

    with pytest.raises(httpx.ConnectError, match="connection refused"):
        transport.fetch_location(
            RemoteLocation("https://example.test/document"),
            destination=tmp_path / "staging",
        )
