# tests/list/list.component.test.py
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apiscope.constants import CONFIG_SCHEMA_REF, LOCAL_CONFIG_SCHEMA_REF
from apiscope.main import app


def _write_config(
    path: Path,
    content: dict[str, object],
    schema_ref: str = CONFIG_SCHEMA_REF,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"$schema": schema_ref, **content}) + "\n", encoding="utf-8")


# validate the selector


def test_list_requires_an_explicit_selector(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["list"], catch_exceptions=False)

    assert result.exit_code == 2
    assert "Missing argument 'SELECTOR'." in result.output


def test_list_rejects_an_unknown_selector(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["list", "markdown"], catch_exceptions=False)

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=list] [code=list.error.invalid_selector] "
        "[selector=markdown]: list selector markdown is invalid. choose all or a supported document type\n"
    )


# list the project registry


def test_list_all_groups_effective_sources_by_type(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    golden: Callable[[str, str], None],
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        isolated_home / ".apiscope" / "config.json",
        {
            "source": {
                "rfc-http": {"doc_type": "rfc", "doc_src": "https://example.test/rfc.txt"},
            },
        },
    )
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "https://example.test/openapi.json"},
            },
        },
    )

    result = CliRunner().invoke(app, ["list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    golden(result.output, "list/grouped-by-type.txt")


def test_list_text_preserves_source_link(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    source = "https://example.test/spec?label=中文%2Fraw"
    _write_config(
        git_project / ".apiscope" / "config.json",
        {"source": {"spec": {"doc_type": "openapi", "doc_src": source}}},
    )

    result = CliRunner().invoke(app, ["list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert f"- [spec] {source}" in result.output


def test_list_filters_one_type_in_json(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "https://example.test/openapi.json"},
                "rfc-http": {"doc_type": "rfc", "doc_src": "./rfc.txt"},
            },
        },
    )

    result = CliRunner().invoke(app, ["--json", "list", "openapi"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "list",
        "meta": {"filter": "openapi"},
        "data": [
            {
                "name": "petstore",
                "type": "openapi",
                "source": "https://example.test/openapi.json",
            }
        ],
        "extra": {"count": 1, "total": 1},
    }


def test_list_uses_the_merged_project_registry(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        isolated_home / ".apiscope" / "config.json",
        {
            "source": {
                "shared": {"doc_type": "openapi", "doc_src": str(isolated_home / "global-shared.json")},
                "global-only": {"doc_type": "repo", "doc_src": str(isolated_home / "global")},
            },
        },
    )
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "shared": {"doc_type": "rfc", "doc_src": "./project-shared.txt"},
                "project-only": {"doc_type": "openapi", "doc_src": "./project-api.json"},
            },
        },
    )
    _write_config(
        git_project / ".apiscope" / "local.json",
        {
            "source": {
                "shared": {"doc_type": "llmstxt", "doc_src": str(git_project / "local-shared.txt")},
                "local-only": {"doc_type": "filesystem", "doc_src": str(git_project / "local")},
            },
        },
        LOCAL_CONFIG_SCHEMA_REF,
    )

    result = CliRunner().invoke(app, ["--json", "list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "list",
        "meta": {"filter": "all"},
        "data": [
            {"name": "local-only", "type": "filesystem", "source": str(git_project / "local")},
            {"name": "shared", "type": "llmstxt", "source": str(git_project / "local-shared.txt")},
            {"name": "project-only", "type": "openapi", "source": "./project-api.json"},
            {"name": "global-only", "type": "repo", "source": str(isolated_home / "global")},
        ],
        "extra": {"count": 4, "total": 4},
    }


# list an empty registry


def test_list_reports_an_empty_project_registry(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    golden: Callable[[str, str], None],
) -> None:
    monkeypatch.chdir(git_project)

    result = CliRunner().invoke(app, ["list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    golden(result.output, "list/empty.txt")


# list the home registry


def test_list_global_reads_only_the_home_registry(
    isolated_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(
        isolated_home / ".apiscope" / "config.json",
        {
            "source": {
                "docs": {"doc_type": "filesystem", "doc_src": str(isolated_home / "docs")},
            },
        },
    )

    result = CliRunner().invoke(app, ["--global", "list", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == (
        "[ok] [scope=home] [action=list] [filter=all]\n\n"
        "---\n\n"
        "[filesystem]\n"
        f"- [docs] {isolated_home / 'docs'}\n\n"
        "---\n\n"
        "[count=1] [total=1]\n"
    )


# window the source list


def test_list_windows_the_sources_by_limit(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    golden: Callable[[str, str], None],
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "./openapi.json"},
                "rfc-http": {"doc_type": "rfc", "doc_src": "./rfc.txt"},
            },
        },
    )

    result = CliRunner().invoke(app, ["list", "all", "--limit", "1"], catch_exceptions=False)

    assert result.exit_code == 0
    golden(result.output, "list/limit.txt")


def test_list_windows_the_sources_by_offset(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    golden: Callable[[str, str], None],
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "./openapi.json"},
                "rfc-http": {"doc_type": "rfc", "doc_src": "./rfc.txt"},
            },
        },
    )

    result = CliRunner().invoke(app, ["list", "all", "--offset", "1"], catch_exceptions=False)

    assert result.exit_code == 0
    golden(result.output, "list/offset.txt")


def test_list_reports_an_empty_window(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    golden: Callable[[str, str], None],
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "./openapi.json"},
            },
        },
    )

    result = CliRunner().invoke(app, ["list", "all", "--offset", "5"], catch_exceptions=False)

    assert result.exit_code == 0
    golden(result.output, "list/empty-window.txt")


def test_list_window_in_json(
    isolated_home: Path,
    git_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(git_project)
    _write_config(
        git_project / ".apiscope" / "config.json",
        {
            "source": {
                "petstore": {"doc_type": "openapi", "doc_src": "./openapi.json"},
                "rfc-http": {"doc_type": "rfc", "doc_src": "./rfc.txt"},
            },
        },
    )

    result = CliRunner().invoke(app, ["--json", "list", "all", "--limit", "1", "--offset", "1"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "list",
        "meta": {"filter": "all", "limit": 1, "offset": 1},
        "data": [
            {"name": "rfc-http", "type": "rfc", "source": "./rfc.txt"},
        ],
        "extra": {"count": 1, "total": 2},
    }
