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
    source = tmp_path / "docs"

    result = CliRunner().invoke(
        app,
        ["--global", "add", "docs", str(source), "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert result.output == "[ok] [scope=home] [action=add] [name=docs] [type=filesystem]\n"
    config = json.loads((isolated_home / ".apiscope" / "config.json").read_text(encoding="utf-8"))
    assert config["source"]["docs"] == {
        "doc_type": "filesystem",
        "doc_src": str(source),
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
        "source docs has an invalid definition, [doc_type] must be one of 'filesystem', 'repo', "
        "'openapi', 'rfc', 'llmstxt' or 'arxiv', but [markdown] was given\n"
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
        "source docs has an invalid definition, [doc_ttl] must be greater than 0, but [0] was given\n"
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


def test_add_rejects_a_duplicate_source_with_another_name(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    runner = CliRunner()

    first = runner.invoke(
        app,
        ["add", "petstore", "https://example.test/openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )
    second = runner.invoke(
        app,
        ["add", "petstore-copy", "https://example.test/openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert second.output == (
        "[error] [scope=project] [action=add] [code=add.error.duplicate_source] [name=petstore] "
        "[source=https://example.test/openapi.json]: "
        "source https://example.test/openapi.json is already registered as petstore\n"
    )
    config = json.loads((git_project / ".apiscope" / "config.json").read_text(encoding="utf-8"))
    assert list(config["source"]) == ["petstore"]


def test_add_rejects_a_duplicate_source_with_another_type(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    runner = CliRunner()

    first = runner.invoke(
        app,
        ["add", "api", "https://example.test/spec.json", "--type", "openapi"],
        catch_exceptions=False,
    )
    second = runner.invoke(
        app,
        ["add", "spec", "https://example.test/spec.json", "--type", "llmstxt"],
        catch_exceptions=False,
    )

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "code=add.error.duplicate_source" in second.output


# require a project for project writes


def test_add_rejects_a_relative_local_path_in_the_home_configuration(
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

    assert result.exit_code == 1
    assert "code=add.error.source_path_absolute" in result.output


def test_add_rejects_an_absolute_local_path_in_the_project_configuration(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "docs", str(git_project / "docs"), "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "code=add.error.source_path_relative" in result.output


def test_add_rejects_an_invalid_source_without_writing(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    config_path = git_project / ".apiscope" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "$schema": CONFIG_SCHEMA_REF,
                "source": {"existing": {"doc_type": "filesystem", "doc_src": "./existing.txt"}},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["add", "docs", "ftp://example.test/docs", "--type", "openapi"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "code=add.error.invalid_source" in result.output
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "docs" not in config["source"]


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
        "[error] [scope=home] [action=add] [code=add.error.project_required]: "
        "a Git project is required unless --global is used\n"
    )


def test_add_rejects_a_name_that_is_not_lowercase_kebab_case(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(
        app,
        ["add", "RuffSite", "./docs", "--type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=add.error.invalid_name] "
        "[name=RuffSite]: source name RuffSite must be lowercase kebab case\n"
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
