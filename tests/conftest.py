# tests/conftest.py

import difflib
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import pytest

from apiscope.constants import APISCOPE_HOME_ENV
from apiscope.sync._lib import transport

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
# common filesystem fixtures
# ==============================================================================


@pytest.fixture
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
