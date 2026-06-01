# tests/conftest.py

from pathlib import Path
from typing import Any

import pytest

import apiscope.config as config_mod
from apiscope.openapi.reader import OpenapiReader

FIXTURE_DIR = Path(__file__).parent / "fixtures"

# ==============================================================================
# config fixtures
# ==============================================================================


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


# ==============================================================================
# openapi reader fixtures
# ==============================================================================


@pytest.fixture(
    scope="session",
    params=["petstore.json", "tictactoe.yaml"],
    ids=["json", "yaml"],
)
def spec_reader(request: pytest.FixtureRequest) -> OpenapiReader:
    return OpenapiReader.load(FIXTURE_DIR / request.param)


@pytest.fixture
def inline_reader() -> OpenapiReader:
    payload: dict[str, Any] = {
        "openapi": "3.0.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/pets": {"get": {"summary": "List"}, "post": {"summary": "Create"}},
            "/pets/{id}": {"get": {"summary": "Get"}, "delete": {"summary": "Delete"}},
        },
    }
    return OpenapiReader(payload)


@pytest.fixture
def ref_reader() -> OpenapiReader:
    payload: dict[str, Any] = {
        "openapi": "3.0.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/pets": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
            },
        },
    }
    return OpenapiReader(payload)
