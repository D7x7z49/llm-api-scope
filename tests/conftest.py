# tests/conftest.py

from pathlib import Path

import pytest

import apiscope.config as config_mod


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    root = tmp_path / ".apiscope"
    root.mkdir()
    return root


@pytest.fixture
def patch_config_paths(monkeypatch, fake_root: Path):
    monkeypatch.setattr(config_mod, "DEFAULT_ROOT", fake_root)
    monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", fake_root / "config.json")
    monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_SCHEMA_PATH", fake_root / "config.schema.json")
