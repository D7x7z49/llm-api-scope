# tests/preflight.unit.test.py

import json
from pathlib import Path

import pytest

from apiscope.constants import (
    APISCOPE_IGNORE_RULE,
    CONFIG_SCHEMA_REF,
    LOCAL_CONFIG_SCHEMA_REF,
)
from apiscope.context import BasePaths, RootOptions, RuntimeContext
from apiscope.preflight import PreflightError, find_project_root, run_preflight, run_read_preflight
from apiscope.schema import LocalSetting, PublicSetting, RuntimeConfig, RuntimeSetting


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
    expected_config = RuntimeConfig(
        source={},
        setting=RuntimeSetting(public=PublicSetting(), local=LocalSetting()),
    ).model_dump(mode="json")

    global_root = isolated_home.resolve() / ".apiscope"
    assert isinstance(context, RuntimeContext)
    assert isinstance(context.paths.home, BasePaths)
    assert isinstance(context.paths.project, BasePaths)
    assert isinstance(context.paths.local, BasePaths)
    assert context.options.global_only is False
    assert context.paths.home.base == isolated_home.resolve()
    assert context.paths.home.root == global_root
    assert context.paths.home.version.read_text(encoding="utf-8") == "1\n"
    assert context.paths.home.cache.is_dir()
    assert context.paths.home.schema.is_file()
    assert context.config.model_dump(mode="json") == expected_config
    assert context.paths.project is not None
    assert context.paths.project.gitignore == git_project / ".gitignore"
    assert context.paths.project.gitignore.read_text(encoding="utf-8") == f"{APISCOPE_IGNORE_RULE}\n"
    assert context.paths.project.config == git_project / ".apiscope" / "config.json"
    assert context.paths.project.schema.is_file()
    assert context.paths.local is not None
    assert context.paths.local.config == git_project / ".apiscope" / "local.json"
    assert context.paths.local.schema.is_file()


def test_run_preflight_writes_scope_specific_schema_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    context = run_preflight(cwd=git_project)

    assert context.paths.project is not None
    assert context.paths.local is not None
    global_schema = json.loads(context.paths.home.schema.read_text(encoding="utf-8"))
    project_schema = json.loads(context.paths.project.schema.read_text(encoding="utf-8"))
    local_schema = json.loads(context.paths.local.schema.read_text(encoding="utf-8"))

    assert global_schema["title"] == "GlobalConfigFile"
    assert project_schema["title"] == "ProjectConfigFile"
    assert local_schema["title"] == "LocalConfigFile"
    assert local_schema["properties"]["$schema"]["minLength"] == 1


def test_run_preflight_global_only_skips_project_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    context = run_preflight(cwd=git_project, options=RootOptions(global_only=True))

    assert context.options.global_only is True
    assert context.paths.project is None
    assert context.paths.local is None
    assert context.paths.home.config.exists()
    assert not (git_project / ".apiscope").exists()


def test_run_preflight_without_a_project_only_creates_global_assets(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    context = run_preflight(cwd=workdir)

    assert context.paths.project is None
    assert context.paths.local is None
    assert context.paths.home.config.exists()


def test_run_preflight_preserves_an_existing_valid_config(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    context = run_preflight(cwd=workdir)
    custom_config = {
        "$schema": CONFIG_SCHEMA_REF,
        "source": {"demo": {"doc_type": "filesystem", "doc_src": str(workdir)}},
        "setting": {"public": {"doc_ttl": 3}, "local": {"proxy": None}},
    }
    context.paths.home.config.write_text(json.dumps(custom_config) + "\n", encoding="utf-8")

    run_preflight(cwd=workdir)

    assert json.loads(context.paths.home.config.read_text(encoding="utf-8")) == custom_config


def test_run_preflight_loads_an_optional_local_config(
    isolated_home: Path,
    git_project: Path,
) -> None:
    context = run_preflight(cwd=git_project)
    assert context.paths.local is not None

    local_config = {
        "$schema": LOCAL_CONFIG_SCHEMA_REF,
        "setting": {"proxy": None},
    }
    context.paths.local.config.write_text(json.dumps(local_config) + "\n", encoding="utf-8")

    context = run_preflight(cwd=git_project)

    assert context.config.setting.local.proxy is None


def test_run_preflight_rejects_an_invalid_version_before_creating_project_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    root = isolated_home / ".apiscope"
    root.mkdir(parents=True)
    version = root / "VERSION"
    version.write_text("2\n", encoding="utf-8")
    gitignore = git_project / ".gitignore"
    gitignore.write_text("# keep this file unchanged\n", encoding="utf-8")

    with pytest.raises(PreflightError, match="VERSION"):
        run_preflight(cwd=git_project)

    assert not (root / "config.json").exists()
    assert gitignore.read_text(encoding="utf-8") == "# keep this file unchanged\n"


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


def test_run_read_preflight_does_not_create_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    context = run_read_preflight(cwd=git_project)
    expected_config = RuntimeConfig(
        source={},
        setting=RuntimeSetting(public=PublicSetting(), local=LocalSetting()),
    ).model_dump(mode="json")

    assert not (isolated_home.resolve() / ".apiscope").exists()
    assert not (git_project / ".apiscope").exists()
    assert context.config.model_dump(mode="json") == expected_config


def test_run_read_preflight_loads_existing_assets(
    isolated_home: Path,
    git_project: Path,
) -> None:
    run_preflight(cwd=git_project)

    context = run_read_preflight(cwd=git_project)

    assert context.paths.project is not None
    assert context.paths.home.config.is_file()
    assert context.paths.project.config.is_file()
    assert context.config.model_dump(mode="json") == RuntimeConfig(
        source={},
        setting=RuntimeSetting(public=PublicSetting(), local=LocalSetting()),
    ).model_dump(mode="json")
