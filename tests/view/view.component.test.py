# tests/view/view.component.test.py

import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from apiscope.main import app


def test_view_shows_a_cached_filesystem_tree(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
    golden: Callable[[str, str], None],
) -> None:
    fixture_tree("filesystem", project_cwd / "docs")
    runner = CliRunner()

    added = runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs"], catch_exceptions=False)

    assert added.exit_code == 0
    assert synced.exit_code == 0
    assert result.exit_code == 0
    golden(result.output, "view/filesystem-tree.txt")


def test_view_path_filter_relays_out_the_index(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    fixture_tree("filesystem", project_cwd / "docs")
    runner = CliRunner()

    added = runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs/api"], catch_exceptions=False)

    assert added.exit_code == 0
    assert synced.exit_code == 0
    assert result.exit_code == 0
    assert "- [1] overview.md" in result.output
    assert "[path=api]" in result.output
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
    runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["--json", "view", "docs"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "status": "ok",
        "scope": "project",
        "action": "view",
        "meta": {"name": "docs", "path": "."},
        "data": [{"index": "1", "key": "README.md", "node_type": "leaf", "path": "README.md"}],
        "extra": {"entries": 1, "cache": "fresh"},
    }


def test_view_depth_caps_the_body(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    fixture_tree("filesystem", project_cwd / "docs")
    runner = CliRunner()

    added = runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["--json", "view", "docs", "--depth", "1"], catch_exceptions=False)

    assert added.exit_code == 0
    assert synced.exit_code == 0
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [item["key"] for item in payload["data"]] == ["api", "README.md"]
    assert payload["meta"] == {"name": "docs", "path": ".", "depth": 1}


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


def test_view_uses_the_projection_error_catalog_directly(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    source.mkdir()
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"], catch_exceptions=False)
    runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "docs/missing.md"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "view_lib.projection.path_not_found" in result.output
    assert "route missing.md does not exist" in result.output
    assert "docs\n- [*][1] README.md" in result.output
    assert "view.error.path_not_found" not in result.output
    assert "Traceback" not in result.output


def test_view_route_error_shows_the_valid_address_and_same_level(
    isolated_home: Path,
    project_cwd: Path,
    document: Callable[[str], str],
) -> None:
    (project_cwd / "openapi.yaml").write_text(document("openapi/view-route.yaml"), encoding="utf-8")
    runner = CliRunner()

    added = runner.invoke(app, ["add", "pets", "openapi.yaml", "--type", "openapi"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "all", "pets"], catch_exceptions=False)
    result = runner.invoke(app, ["view", "pets/pets/x"], catch_exceptions=False)

    assert added.exit_code == 0
    assert synced.exit_code == 0
    assert result.exit_code == 1
    assert "route pets/x does not exist" in result.output
    assert "pets/pets\n" in result.output
    assert "- [*][1] GET: List pets" in result.output
    assert "- [/][3] {petId}" in result.output
