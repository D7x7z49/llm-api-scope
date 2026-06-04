# tests/openapi/app.component.test.py
#
# component test for the operation commands in openapi/app.py.
# exercises _get_reader, _resolve_source, _load_reader indirectly.

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apiscope.config import Config
from apiscope.main import app

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def patch_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / ".apiscope"
    config_path = root / "config.json"

    monkeypatch.setattr("apiscope.config.DEFAULT_ROOT", root)
    monkeypatch.setattr("apiscope.config.DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setattr("apiscope.config.CACHE_ROOT", root / "cache")

    root.mkdir(parents=True)
    Config().write(config_path)

    return config_path


def test_show_info_with_file_path(runner: CliRunner, patch_config: Path) -> None:
    """Direct file path source outputs metadata json without paths."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    result = runner.invoke(app, ["openapi", "info", petstore])

    assert result.exit_code == 0

    meta = json.loads(result.stdout)
    assert "openapi" in meta
    assert "info" in meta
    assert "servers" in meta
    assert "tags" in meta
    assert "paths" not in meta
    assert "components" not in meta


def test_show_info_with_alias(runner: CliRunner, patch_config: Path) -> None:
    """Registered alias resolves and outputs metadata json."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    with Config.edit(patch_config) as cfg:
        cfg.openapi.alias["petstore"] = petstore

    result = runner.invoke(app, ["openapi", "info", "petstore"])

    assert result.exit_code == 0

    meta = json.loads(result.stdout)
    assert meta["info"]["title"] == "Swagger Petstore - OpenAPI 3.0"


def test_list_all_operations(runner: CliRunner, patch_config: Path) -> None:
    """List returns paginated result with items array."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    result = runner.invoke(app, ["openapi", "list", petstore])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert "items" in data
    ops = data["items"]
    assert isinstance(ops, list)
    assert len(ops) > 0
    for op in ops:
        assert "path" in op
        assert "method" in op
        assert "summary" in op
        assert "operationId" in op
        assert "tags" in op


def test_list_filter_by_tag(runner: CliRunner, patch_config: Path) -> None:
    """--tag filter returns only matching operations."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    result = runner.invoke(app, ["openapi", "list", petstore, "--tag", "store"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["total"] == 4
    ops = data["items"]
    assert len(ops) == 4
    for op in ops:
        assert "store" in op["tags"]


def test_describe_operation_full(runner: CliRunner, patch_config: Path) -> None:
    """Describe returns full operation with responses resolved."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    result = runner.invoke(app, ["openapi", "describe", petstore, "/pet/{petId}", "get"])

    assert result.exit_code == 0
    op = json.loads(result.stdout)
    assert op["operationId"] == "getPetById"
    assert "responses" in op
    assert len(op["parameters"]) == 1


def test_describe_operation_request_only(runner: CliRunner, patch_config: Path) -> None:
    """--request flag strips responses from output."""
    petstore = str(FIXTURE_DIR / "petstore.json")
    result = runner.invoke(
        app, ["openapi", "describe", petstore, "/pet/{petId}", "get", "--request"]
    )

    assert result.exit_code == 0
    op = json.loads(result.stdout)
    assert "responses" not in op
    assert op["operationId"] == "getPetById"


def test_describe_merges_path_item_params(runner: CliRunner, patch_config: Path) -> None:
    """Path-item parameters merge with operation parameters."""
    tictactoe = str(FIXTURE_DIR / "tictactoe.yaml")
    result = runner.invoke(app, ["openapi", "describe", tictactoe, "/board/{row}/{column}", "put"])

    assert result.exit_code == 0
    op = json.loads(result.stdout)
    param_names = [p["name"] for p in op["parameters"]]
    # row and column from path-item, progressUrl from operation
    assert "row" in param_names
    assert "column" in param_names
    assert "progressUrl" in param_names
