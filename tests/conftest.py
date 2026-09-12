# tests/conftest.py

from pathlib import Path

import pytest

from apiscope.constants import APISCOPE_HOME_ENV

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
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    return project
