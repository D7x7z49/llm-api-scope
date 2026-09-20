# tests/config.unit.test.py
from apiscope.config import assemble_runtime_config
from apiscope.constants import CONFIG_SCHEMA_REF
from apiscope.schema import GlobalConfigFile, LocalConfigFile, ProjectConfigFile


def _config_data(**values: object) -> dict[str, object]:
    return {"$schema": CONFIG_SCHEMA_REF, **values}


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
