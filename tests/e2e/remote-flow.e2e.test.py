# tests/e2e/remote-flow.e2e.test.py

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def test_remote_openapi_source_flows_from_add_to_read(
    document_path,
    loopback,
    e2e_project: Path,
    run_cli,
) -> None:
    base = loopback(document_path("openapi"))

    added = run_cli(["add", "api", f"{base}/openapi.yaml", "--type", "openapi"], e2e_project)
    synced = run_cli(["sync", "all", "api"], e2e_project)
    viewed = run_cli(["--json", "view", "api"], e2e_project)

    assert added.returncode == 0, added.stderr
    assert synced.returncode == 0, synced.stderr
    assert viewed.returncode == 0, viewed.stderr

    nodes = json.loads(viewed.stdout)["data"]
    operation = next(node for node in nodes if node.get("path") == "pets/GET")
    read = run_cli(["--json", "read", "api", operation["index"]], e2e_project)

    assert read.returncode == 0, read.stderr
    payload = json.loads(read.stdout)
    assert payload["status"] == "ok"
    assert payload["meta"] == {"name": "api", "target": "pets/GET"}
    assert payload["data"][0]["media_type"] == "application/yaml"
    assert "get:" in payload["data"][0]["content"]
