# tests/e2e/filesystem-flow.e2e.test.py

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def test_filesystem_source_flows_from_add_to_read(
    fixture_tree,
    e2e_project: Path,
    run_cli,
) -> None:
    fixture_tree("filesystem", e2e_project / "docs")

    added = run_cli(["add", "docs", "docs", "--type", "filesystem"], e2e_project)
    synced = run_cli(["sync", "all", "docs"], e2e_project)
    viewed = run_cli(["--json", "view", "docs"], e2e_project)

    assert added.returncode == 0, added.stderr
    assert synced.returncode == 0, synced.stderr
    assert viewed.returncode == 0, viewed.stderr

    nodes = json.loads(viewed.stdout)["data"]
    leaf = next(node for node in nodes if node.get("path") == "README.md")
    read = run_cli(["--json", "read", "docs", leaf["index"]], e2e_project)

    assert read.returncode == 0, read.stderr
    payload = json.loads(read.stdout)
    assert payload["status"] == "ok"
    assert payload["meta"] == {"name": "docs", "target": "README.md"}
    assert payload["data"][0]["kind"] == "markdown"
    assert "API documentation" in payload["data"][0]["content"]
