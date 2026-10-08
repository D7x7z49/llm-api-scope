# tests/conftest.py

import difflib
import functools
import os
import shutil
import threading
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Literal

import httpx2
import pytest

from apiscope.cache import CacheMetadata
from apiscope.constants import APISCOPE_HOME_ENV
from apiscope.schema import DocumentType
from apiscope.sync._lib import transport
from apiscope.view_lib.schema import IndexedNode, NodeType

# ==============================================================================
# fixture data
# ==============================================================================

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DOCUMENTS = FIXTURES / "documents"
GOLDEN = FIXTURES / "golden"


@pytest.fixture
def document() -> Callable[[str], str]:
    def load(name: str) -> str:
        return (DOCUMENTS / name).read_text(encoding="utf-8")

    return load


@pytest.fixture
def document_path() -> Callable[[str], Path]:
    def path(name: str) -> Path:
        return DOCUMENTS / name

    return path


@pytest.fixture
def fixture_tree() -> Callable[[str, Path], Path]:
    def copy(name: str, destination: Path) -> Path:
        shutil.copytree(DOCUMENTS / name, destination)
        return destination

    return copy


@pytest.fixture
def golden() -> Callable[[str, str], None]:
    def check(actual: str, name: str) -> None:
        path = GOLDEN / name
        if os.environ.get("UPDATE_GOLDEN") == "1":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(actual, encoding="utf-8")
            return
        if not path.is_file():
            pytest.fail(f"golden file is missing: {name}; run with UPDATE_GOLDEN=1")
        expected = path.read_text(encoding="utf-8")
        if actual == expected:
            return
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile=f"{name} expected",
                tofile=f"{name} actual",
                lineterm="",
            )
        )
        pytest.fail(f"golden mismatch for {name}\n{diff}")

    return check


# ==============================================================================
# common data builders
# ==============================================================================


@pytest.fixture
def indexed_node() -> Callable[..., IndexedNode]:
    def build(
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

    return build


@pytest.fixture
def cache_metadata() -> Callable[..., CacheMetadata]:
    def build(
        doc_type: DocumentType,
        *,
        content_kind: Literal["file", "directory"] = "file",
        content_name: str | None = None,
        source: str = "file:///source",
    ) -> CacheMetadata:
        return CacheMetadata(
            format_version="1",
            doc_type=doc_type,
            source=source,
            source_digest="digest",
            fetched_at=datetime.now(timezone.utc),
            content_kind=content_kind,
            content_name=content_name,
            content_digest="digest",
        )

    return build


# ==============================================================================
# common network fixtures
# ==============================================================================


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def loopback() -> Iterator[Callable[[Path], str]]:
    servers: list[tuple[ThreadingHTTPServer, threading.Thread]] = []

    def serve(directory: Path) -> str:
        handler = functools.partial(_QuietHandler, directory=str(directory))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield serve

    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


# ==============================================================================
# common filesystem fixtures
# ==============================================================================


# autouse: a test must not read or write the real apiscope home
@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "isolated-home"
    monkeypatch.setenv(APISCOPE_HOME_ENV, str(home))
    return home


@pytest.fixture
def git_project(tmp_path: Path) -> Path:
    # This is a project-root marker, not a real Git repository.
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    return project


@pytest.fixture
def project_cwd(git_project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(git_project)
    return git_project


@pytest.fixture
def git_executable() -> str:
    executable = shutil.which("git")
    if executable is None:
        pytest.skip("requires the system git executable")
    return executable


@pytest.fixture
def http_client_options() -> dict[str, Any]:
    return {}


@pytest.fixture
def install_mock_client(
    monkeypatch: pytest.MonkeyPatch,
    http_client_options: dict[str, Any],
) -> Callable[[Callable[[httpx2.Request], httpx2.Response]], None]:
    real_client = httpx2.Client

    def install(handler: Callable[[httpx2.Request], httpx2.Response]) -> None:
        def client_factory(**kwargs: Any) -> httpx2.Client:
            http_client_options.update(kwargs)
            mock_kwargs = dict(kwargs)
            mock_kwargs.pop("proxy", None)
            return real_client(transport=httpx2.MockTransport(handler), **mock_kwargs)

        monkeypatch.setattr(transport.httpx2, "Client", client_factory)

    return install
