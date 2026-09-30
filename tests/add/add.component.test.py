# tests/add/add.component.test.py
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apiscope.constants import CONFIG_SCHEMA_REF
from apiscope.main import app

# write project sources


def test_add_writes_a_project_source(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "petstore", "https://example.test/openapi.json", "--type", "openapi", "--ttl", "14"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert result.output == "[ok] [scope=project] [action=add] [name=petstore] [type=openapi]\n"
    config = json.loads((git_project / ".apiscope" / "config.json").read_text(encoding="utf-8"))
    assert config["source"]["petstore"] == {
        "doc_type": "openapi",
        "doc_src": "https://example.test/openapi.json",
        "doc_ttl": 14,
    }


def test_add_can_render_a_json_report(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["--json", "add", "petstore", "./openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "add",
        "meta": {"name": "petstore", "type": "openapi"},
    }


def test_add_preserves_existing_configuration_sections(
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
                    "existing": {"doc_type": "rfc", "doc_src": "./existing.txt"},
                },
                "setting": {"doc_ttl": 11},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["add", "new", "./new.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["source"]["existing"] == {
        "doc_type": "rfc",
        "doc_src": "./existing.txt",
        "doc_ttl": None,
    }
    assert config["source"]["new"] == {
        "doc_type": "filesystem",
        "doc_src": "./new.txt",
        "doc_ttl": None,
    }
    assert config["setting"] == {"doc_ttl": 11}


# write home sources


def test_add_global_writes_a_home_source(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        ["--global", "add", "docs", "./docs", "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert result.output == "[ok] [scope=home] [action=add] [name=docs] [type=filesystem]\n"
    config = json.loads((isolated_home / ".apiscope" / "config.json").read_text(encoding="utf-8"))
    assert config["source"]["docs"] == {
        "doc_type": "filesystem",
        "doc_src": "./docs",
        "doc_ttl": None,
    }


# validate source options and conflicts


def test_add_rejects_an_unknown_document_type(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "docs", "./docs", "--type", "markdown"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=add.error.invalid_options] [name=docs]: "
        "source docs has an invalid definition. check its type, location, and TTL\n"
    )


def test_add_rejects_a_non_positive_ttl(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "docs", "./docs", "--type", "filesystem", "--ttl", "0"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=add.error.invalid_options] [name=docs]: "
        "source docs has an invalid definition. check its type, location, and TTL\n"
    )


def test_add_rejects_a_duplicate_name_without_changing_the_source(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    runner = CliRunner()
    arguments = ["add", "petstore", "https://example.test/openapi.json", "--type", "openapi"]

    first = runner.invoke(app, arguments, catch_exceptions=False)
    second = runner.invoke(
        app,
        ["add", "petstore", "https://example.test/other.json", "--type", "openapi"],
        catch_exceptions=False,
    )

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert second.output == (
        "[error] [scope=project] [action=add] [code=add.error.duplicate_name] [name=petstore]: "
        "source petstore already exists\n"
    )
    config = json.loads((git_project / ".apiscope" / "config.json").read_text(encoding="utf-8"))
    assert config["source"]["petstore"]["doc_src"] == "https://example.test/openapi.json"


# require a project for project writes


def test_add_requires_a_project_without_global_mode(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        ["add", "docs", "./docs", "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=add.error.project_required]: "
        "a Git project is required unless --global is used\n"
    )


def test_add_rejects_the_reserved_name(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "all", "./docs", "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=add.error.reserved_name] [name=all]: source name all is reserved\n"
    )
