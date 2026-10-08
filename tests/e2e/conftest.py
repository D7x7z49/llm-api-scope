# tests/e2e/conftest.py

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

PROXY_VARS = (
    "ALL_PROXY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "all_proxy",
    "http_proxy",
    "https_proxy",
    "no_proxy",
)


@pytest.fixture(scope="session")
def apiscope_cli() -> Path:
    script = Path(sys.executable).with_name("apiscope")
    if not script.is_file():
        pytest.fail("the apiscope console script is missing; run pdm install")
    return script


@pytest.fixture
def e2e_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def e2e_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    return project


def _environment(home: Path) -> dict[str, str]:
    # a clean environment keeps the real home and any proxy out of the run
    env = {
        "APISCOPE_HOME": str(home),
        "HOME": str(home),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    for name in PROXY_VARS:
        env.pop(name, None)
    return env


@pytest.fixture
def run_cli(
    apiscope_cli: Path,
    e2e_home: Path,
) -> Callable[[list[str], Path], subprocess.CompletedProcess[str]]:
    def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(apiscope_cli), *args],
            cwd=cwd,
            env=_environment(e2e_home),
            text=True,
            capture_output=True,
        )

    return run
