# tests/preflight.unit.test.py

import json
from pathlib import Path

import pytest

from apiscope.constants import CONFIG_VERSION
from apiscope.context import CommandContext
from apiscope.preflight import PreflightError, find_project_root, run_preflight
from apiscope.schema import ConfigSchema


def test_find_project_root_returns_the_nearest_git_ancestor(git_project: Path) -> None:
    nested = git_project / "nested" / "work"
    nested.mkdir(parents=True)

    assert find_project_root(nested) == git_project.resolve()


def test_find_project_root_accepts_a_git_worktree_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    nested = project / "nested"
    project.mkdir()
    (project / ".git").write_text("gitdir: /tmp/example-worktree\n", encoding="utf-8")
    nested.mkdir()

    assert find_project_root(nested) == project.resolve()


def test_run_preflight_uses_apiscope_home_and_creates_project_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    context = run_preflight(cwd=git_project)
    expected_config = ConfigSchema(version=CONFIG_VERSION, sources={}, settings={}).model_dump(mode="json")

    global_root = isolated_home.resolve() / ".apiscope"
    assert isinstance(context, CommandContext)
    assert context.global_paths.home == isolated_home.resolve()
    assert context.global_paths.root == global_root
    assert context.global_paths.version.read_text(encoding="utf-8") == "1\n"
    assert context.global_paths.cache.is_dir()
    assert context.global_config.model_dump(mode="json") == expected_config
    assert context.project_paths is not None
    assert context.project_paths.config == git_project / ".apiscope" / "config.json"
    assert context.project_config is not None
    assert context.project_config.model_dump(mode="json") == expected_config


def test_run_preflight_without_a_project_only_creates_global_assets(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    context = run_preflight(cwd=workdir)

    assert context.project_paths is None
    assert context.project_config is None
    assert context.global_paths.config.exists()


def test_run_preflight_preserves_an_existing_valid_config(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    context = run_preflight(cwd=workdir)
    custom_config = {
        "version": CONFIG_VERSION,
        "sources": {"demo": {"type": "filesystem", "src": "."}},
        "settings": {"cache_ttl": 3},
    }
    context.global_paths.config.write_text(json.dumps(custom_config) + "\n", encoding="utf-8")

    run_preflight(cwd=workdir)

    assert json.loads(context.global_paths.config.read_text(encoding="utf-8")) == custom_config


def test_run_preflight_rejects_an_invalid_version_before_creating_config(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    root = isolated_home / ".apiscope"
    root.mkdir(parents=True)
    version = root / "VERSION"
    version.write_text("2\n", encoding="utf-8")

    with pytest.raises(PreflightError, match="VERSION"):
        run_preflight(cwd=tmp_path)

    assert not (root / "config.json").exists()


def test_run_preflight_preserves_an_invalid_config_and_reports_its_path(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    root = isolated_home / ".apiscope"
    root.mkdir(parents=True)
    config = root / "config.json"
    invalid_content = "{invalid\n"
    config.write_text(invalid_content, encoding="utf-8")

    with pytest.raises(PreflightError, match=r"config\.json"):
        run_preflight(cwd=tmp_path)

    assert config.read_text(encoding="utf-8") == invalid_content
