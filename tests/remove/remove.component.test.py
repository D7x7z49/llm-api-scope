# tests/remove/remove.component.test.py
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apiscope.constants import CONFIG_SCHEMA_REF
from apiscope.main import app

# delete a project source


def test_remove_deletes_only_the_selected_project_source(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    config_path = git_project / ".apiscope" / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "$schema": CONFIG_SCHEMA_REF,
                "source": {
                    "one": {"doc_type": "filesystem", "doc_src": "./one"},
                    "two": {"doc_type": "filesystem", "doc_src": "./two"},
                },
                "setting": {"doc_ttl": 11},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["remove", "one"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == "[ok] [scope=project] [action=remove] [name=one]\n"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "one" not in config["source"]
    assert config["source"]["two"] == {
        "doc_type": "filesystem",
        "doc_src": "./two",
        "doc_ttl": None,
    }
    assert config["setting"] == {"doc_ttl": 11}


# delete a home source


def test_remove_global_deletes_a_home_source(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = isolated_home / ".apiscope" / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "$schema": CONFIG_SCHEMA_REF,
                "source": {
                    "docs": {"doc_type": "filesystem", "doc_src": "./docs"},
                    "api": {"doc_type": "openapi", "doc_src": "./api.json"},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["--global", "remove", "docs"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == "[ok] [scope=home] [action=remove] [name=docs]\n"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "docs" not in config["source"]
    assert config["source"]["api"] == {
        "doc_type": "openapi",
        "doc_src": "./api.json",
        "doc_ttl": None,
    }


# report missing sources


def test_remove_reports_a_missing_source(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["remove", "missing"], catch_exceptions=False)

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=remove] [code=remove.error.name_not_found] [name=missing]: "
        "source missing was not found\n"
    )


# require a project for project deletion


def test_remove_requires_a_project_without_global_mode(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["remove", "docs"], catch_exceptions=False)

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=home] [action=remove] [code=remove.error.project_required]: "
        "a Git project is required unless --global is used\n"
    )


def test_remove_rejects_the_reserved_name(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["remove", "all"], catch_exceptions=False)

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=remove] [code=remove.error.reserved_name] [name=all]: "
        "source name all is reserved\n"
    )
