# tests/config.unit.test.py

import json
from pathlib import Path

import pytest

import apiscope.config as config_module
from apiscope.config import ConfigError, assemble_runtime_config, save_config_file
from apiscope.constants import CONFIG_SCHEMA_REF
from apiscope.schema import GlobalConfigFile, LocalConfigFile, ProjectConfigFile


def _config_data(**values: object) -> dict[str, object]:
    return {"$schema": CONFIG_SCHEMA_REF, **values}


def test_save_config_file_keeps_the_original_when_replacement_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.json"
    path.write_text("original\n", encoding="utf-8")
    config_file = GlobalConfigFile.model_validate(_config_data())

    def fail_replace(source: str, destination: Path) -> None:
        raise OSError(f"cannot replace {source} with {destination}")

    monkeypatch.setattr(config_module.os, "replace", fail_replace)

    with pytest.raises(ConfigError, match="cannot write"):
        save_config_file(path, config_file)

    assert path.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".config.json.*.tmp")) == []


def test_save_config_file_writes_schema_before_configuration_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config_file = GlobalConfigFile.model_validate(
        _config_data(source={"docs": {"doc_type": "filesystem", "doc_src": "docs"}})
    )

    save_config_file(path, config_file)

    content = path.read_text(encoding="utf-8")
    assert list(json.loads(content)) == ["$schema", "source"]


def test_assemble_runtime_config_merges_sources_and_settings() -> None:
    global_file = GlobalConfigFile.model_validate(
        _config_data(
            source={
                "shared": {"doc_type": "filesystem", "doc_src": "global"},
                "global": {"doc_type": "repo", "doc_src": "global-repo"},
            },
            setting={"public": {"doc_ttl": 14}, "local": {"proxy": "http://proxy"}},
        )
    )
    project_file = ProjectConfigFile.model_validate(
        _config_data(
            source={
                "shared": {"doc_type": "filesystem", "doc_src": "project"},
                "project": {"doc_type": "openapi", "doc_src": "project-api"},
            },
            setting={"doc_ttl": 3},
        )
    )
    local_file = LocalConfigFile.model_validate(
        _config_data(
            source={
                "shared": {"doc_type": "filesystem", "doc_src": "local"},
                "local": {"doc_type": "rfc", "doc_src": "local-rfc"},
            },
            setting={"proxy": None},
        )
    )

    config = assemble_runtime_config(global_file, project_file, local_file)

    assert config.source["shared"].doc_src == "local"
    assert config.source["global"].doc_src == "global-repo"
    assert config.source["project"].doc_src == "project-api"
    assert config.source["local"].doc_src == "local-rfc"
    assert config.setting.public.doc_ttl == 3
    assert config.setting.local.proxy is None


def test_assemble_runtime_config_preserves_inherited_fields_from_empty_scope_settings() -> None:
    global_file = GlobalConfigFile.model_validate(
        _config_data(
            setting={"public": {"doc_ttl": 14}, "local": {"proxy": "http://proxy"}},
        )
    )
    project_file = ProjectConfigFile.model_validate(_config_data(setting={}))
    local_file = LocalConfigFile.model_validate(_config_data(setting={}))

    project_config = assemble_runtime_config(global_file, project_file)
    local_config = assemble_runtime_config(global_file, None, local_file)

    assert project_config.setting.public.doc_ttl == 14
    assert project_config.setting.local.proxy == "http://proxy"
    assert local_config.setting.public.doc_ttl == 14
    assert local_config.setting.local.proxy == "http://proxy"


def test_assemble_runtime_config_uses_defaults_when_sections_are_missing() -> None:
    global_file = GlobalConfigFile.model_validate(_config_data())

    config = assemble_runtime_config(global_file)

    assert config.source == {}
    assert config.setting.public.doc_ttl == 7
    assert config.setting.local.proxy is None


def test_assemble_runtime_config_preserves_source_ttl_fallback_value() -> None:
    global_file = GlobalConfigFile.model_validate(
        _config_data(
            source={
                "docs": {
                    "doc_type": "filesystem",
                    "doc_src": "docs",
                    "doc_ttl": None,
                }
            },
            setting={"public": {"doc_ttl": 9}, "local": {"proxy": None}},
        )
    )

    config = assemble_runtime_config(global_file)

    assert config.source["docs"].doc_ttl is None
    assert config.setting.public.doc_ttl == 9


def test_local_config_accepts_source_entries() -> None:
    config = LocalConfigFile.model_validate(
        _config_data(
            source={"docs": {"doc_type": "filesystem", "doc_src": "docs"}},
        )
    )

    assert config.model_dump()["source"]["docs"]["doc_src"] == "docs"
