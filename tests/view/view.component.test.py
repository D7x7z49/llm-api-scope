# tests/view/view.component.test.py
# ruff: noqa: N999

import json
from pathlib import Path

from typer.testing import CliRunner

from apiscope.main import app


def test_view_shows_a_cached_filesystem_tree(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    (source / "api").mkdir(parents=True)
    (source / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    added = runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs"], catch_exceptions=False)

    assert added.exit_code == 0
    assert synced.exit_code == 0
    assert result.exit_code == 0
    assert result.output == (
        "[ok] [scope=project] [action=view] [name=docs] [path=.]\n\n"
        "---\n\n"
        "- [1] api\n"
        "- [1.1] overview.md\n"
        "- [2] README.md\n"
        "\n---\n\n"
        "{\n"
        '  "entries": 3,\n'
        '  "cache": "fresh",\n'
        '  "index": "temporary"\n'
        "}\n"
    )


def test_view_path_filter_keeps_the_complete_tree_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    (source / "api").mkdir(parents=True)
    (source / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs", "api"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "- [1] api" in result.output
    assert "- [1.1] overview.md" in result.output
    assert "README.md" not in result.output


def test_view_json_contains_the_same_semantic_nodes(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    source.mkdir()
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["--json", "view", "docs"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "view",
        "meta": {"name": "docs", "path": "."},
        "data": [{"index": "1", "kind": "value", "value": "README.md"}],
        "extra": {"entries": 1, "cache": "fresh", "index": "temporary"},
    }


def test_view_reports_a_missing_cache(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("docs\n", encoding="utf-8")
    runner = CliRunner()

    runner.invoke(app, ["add", "docs", "docs.txt", "--type", "filesystem"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "view.error.cache_missing" in result.output
    assert "sync it before retrying" in result.output
