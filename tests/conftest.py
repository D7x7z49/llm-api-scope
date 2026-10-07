# tests/conftest.py

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import pytest

from apiscope.constants import APISCOPE_HOME_ENV
from apiscope.sync._lib import transport

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
