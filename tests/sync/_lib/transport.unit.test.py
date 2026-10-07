# tests/sync/_lib/transport.unit.test.py
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import pytest

from apiscope.cache import digest_content
from apiscope.sync._lib import transport
from apiscope.sync._lib.schema import RemoteLocation


def test_fetch_location_writes_redirected_remote_content(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.url.path == "/spec.json":
            return httpx2.Response(302, headers={"Location": "/final.json"})
        return httpx2.Response(200, content=b'{"openapi":"3.1.0"}')

    install_mock_client(handler)
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


def test_fetch_location_passes_a_proxy_to_the_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: dict[str, Any] = {}

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
            del exception_type, exception, traceback

        def get(self, url: str) -> httpx2.Response:
            return httpx2.Response(200, request=httpx2.Request("GET", url), content=b"rfc")

    def client_factory(**kwargs: Any) -> FakeClient:
        options.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(transport.httpx2, "Client", client_factory)

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

        def get(self, url: str) -> httpx2.Response:
            return httpx2.Response(200, request=httpx2.Request("GET", url), content=b"direct")

    def client_factory(**kwargs: Any) -> FakeClient:
        options.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(transport.httpx2, "Client", client_factory)

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
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
    http_client_options: dict[str, Any],
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://environment.example.test:8080")
    monkeypatch.setenv("NO_PROXY", "example.test")
    install_mock_client(lambda request: httpx2.Response(200, request=request, content=b"direct"))

    transport.fetch_location(
        RemoteLocation("https://example.test/document"),
        destination=tmp_path / "staging",
    )

    assert http_client_options == {
        "follow_redirects": True,
        "timeout": transport.HTTP_TIMEOUT_SECONDS,
        "trust_env": False,
    }


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(httpx2.Response(404, content=b"missing"), id="status-error"),
        pytest.param(httpx2.Response(503, content=b"unavailable"), id="server-error"),
    ],
)
def test_fetch_location_propagates_http_status_errors(
    tmp_path: Path,
    response: httpx2.Response,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    install_mock_client(lambda request: response)

    with pytest.raises(httpx2.HTTPStatusError):
        transport.fetch_location(
            RemoteLocation("https://example.test/document"),
            destination=tmp_path / "staging",
        )


def test_fetch_location_propagates_http_transport_errors(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connection refused", request=request)

    install_mock_client(handler)

    with pytest.raises(httpx2.ConnectError, match="connection refused"):
        transport.fetch_location(
            RemoteLocation("https://example.test/document"),
            destination=tmp_path / "staging",
        )
