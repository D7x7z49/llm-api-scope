# tests/openapi/spec.component.test.py
#
# Component test for the apiscope/openapi/spec/ package.
# Named spec.component.test.py (not spec/app.component.test.py) because
# this tests the spec component as a whole, not a specific source file.

import json
from pathlib import Path

import pytest

from apiscope.config import Config


def _bootstrap_config(path: Path) -> None:
    Config().write(path)


def test_add_alias_to_new_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Write alias to config and verify it persists on disk."""
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr("apiscope.config.DEFAULT_CONFIG_PATH", cfg_path)
    _bootstrap_config(cfg_path)

    with Config.edit(cfg_path) as cfg:
        cfg.openapi.alias["gh"] = "https://api.github.com"

    data = json.loads(cfg_path.read_text())
    assert data["openapi"]["alias"]["gh"] == "https://api.github.com"


def test_remove_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove alias from config and verify it is gone after re-open."""
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr("apiscope.config.DEFAULT_CONFIG_PATH", cfg_path)
    _bootstrap_config(cfg_path)

    with Config.edit(cfg_path) as cfg:
        cfg.openapi.alias["gh"] = "https://api.github.com"

    with Config.edit(cfg_path) as cfg:
        del cfg.openapi.alias["gh"]

    with Config.edit(cfg_path) as cfg:
        assert "gh" not in cfg.openapi.alias


def test_list_aliases_project_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Project alias overrides global on same key; global-only keys survive."""
    global_path = tmp_path / "global.json"
    project_path = tmp_path / "project.json"
    monkeypatch.setattr("apiscope.config.DEFAULT_CONFIG_PATH", global_path)
    monkeypatch.setattr("apiscope.config.get_project_config_path", lambda: project_path)
    _bootstrap_config(global_path)
    _bootstrap_config(project_path)

    with Config.edit(global_path) as cfg:
        cfg.openapi.alias["gh"] = "https://global.url"
        cfg.openapi.alias["gitlab"] = "https://gitlab.com"

    with Config.edit(project_path) as cfg:
        cfg.openapi.alias["gh"] = "https://project.url"

    global_cfg = Config.model_validate_json(global_path.read_text())
    project_cfg = Config.model_validate_json(project_path.read_text())
    merged = global_cfg.openapi.alias | project_cfg.openapi.alias

    assert merged["gh"] == "https://project.url"
    assert merged["gitlab"] == "https://gitlab.com"
