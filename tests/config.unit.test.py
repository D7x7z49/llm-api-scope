# tests/config.unit.test.py

import time

import apiscope.config as config_mod


class TestBaseConfigStale:
    def test_is_stale_path_missing_file(self, tmp_path):
        cfg = config_mod.BaseConfig(cache_ttl=60)
        missing = tmp_path / "nonexistent.txt"

        assert cfg.is_stale_path(missing) is True

    def test_is_stale_since_expired(self, monkeypatch):
        cfg = config_mod.BaseConfig(cache_ttl=60)
        monkeypatch.setattr(time, "time", lambda: 1e10)
        assert cfg.is_stale_since(0.0) is True

    def test_is_stale_since_recent(self):
        cfg = config_mod.BaseConfig(cache_ttl=999999)
        assert cfg.is_stale_since(time.time() - 1) is False


class TestGetConfigFresh:
    def test_creates_files_on_first_run(self, patch_config_paths, monkeypatch):
        monkeypatch.setattr(config_mod, "_get_project_root", lambda: None)
        cfg = config_mod.get_config()

        assert cfg.openapi.alias == {}
        assert config_mod.DEFAULT_CONFIG_PATH.exists()
        assert config_mod.DEFAULT_CONFIG_SCHEMA_PATH.exists()


class TestGetConfigGlobal:
    def test_loads_global_aliases(self, patch_config_paths, monkeypatch):
        config_mod.DEFAULT_CONFIG_PATH.write_text(
            '{"openapi": {"alias": {"gh": "remote:https://api.github.com"}}}'
        )
        monkeypatch.setattr(config_mod, "_get_project_root", lambda: None)

        cfg = config_mod.get_config()
        assert cfg.openapi.alias == {"gh": "remote:https://api.github.com"}


class TestGetConfigProject:
    def test_project_overrides_global(self, patch_config_paths, monkeypatch, tmp_path):
        config_mod.DEFAULT_CONFIG_PATH.write_text(
            '{"openapi": {"alias": {"gh": "remote:https://api.github.com"}}}'
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / ".apiscope.config.json"
        project_config.write_text('{"openapi": {"alias": {"gh": "local:./openapi.json"}}}')
        monkeypatch.setattr(config_mod, "_get_project_root", lambda: project_dir)

        cfg = config_mod.get_config()
        assert cfg.openapi.alias == {"gh": "local:./openapi.json"}


class TestGetProjectRoot:
    def test_finds_git_root(self, tmp_path, monkeypatch):
        git_dir = tmp_path / "repo"
        git_dir.mkdir()
        (git_dir / ".git").mkdir()
        monkeypatch.chdir(git_dir)

        assert config_mod._get_project_root() == git_dir.resolve()

    def test_returns_none_when_no_git(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert config_mod._get_project_root() is None
