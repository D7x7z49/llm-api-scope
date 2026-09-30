# tests/app.component.test.py
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apiscope.main import app

# report preflight failures


def test_callback_reports_a_preflight_error_at_the_cli_boundary(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = isolated_home / ".apiscope" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text("{invalid\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, [], catch_exceptions=False)

    assert result.exit_code == 1
    assert "configuration at" in result.output
    assert "Traceback" not in result.output


# prepare a project context


def test_callback_prepares_context_for_a_project(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["sync"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (isolated_home / ".apiscope" / "config.json").exists()
    assert (git_project / ".apiscope" / "config.json").exists()


# skip project preparation in global mode


def test_global_option_skips_project_preparation(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["--global", "sync"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (isolated_home / ".apiscope" / "config.json").exists()
    assert not (git_project / ".apiscope").exists()


# read commands stay read-only


def test_read_command_does_not_prepare_assets(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert not (isolated_home / ".apiscope").exists()
    assert not (git_project / ".apiscope").exists()
