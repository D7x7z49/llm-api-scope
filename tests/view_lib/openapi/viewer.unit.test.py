# tests/view_lib/openapi/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.openapi.viewer import OpenapiViewer


def test_openapi_viewer_keeps_path_hints_and_method_order(
    tmp_path: Path,
    document: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(document("openapi/viewer.yaml"), encoding="utf-8")

    tree = OpenapiViewer().build(content, cache_metadata("openapi", content_name="openapi.yaml"))

    assert tree.resolve("pets/").path == "pets"
    assert [(node.index, node.description, node.key) for node in tree.indexed()] == [
        ("1", "pet collection", "pets"),
        ("1.1", "list pets", "GET"),
        ("1.2", "query pets", "QUERY"),
        ("1.3", "copy pets", "COPY"),
        ("1.4", "one pet", "{petId}"),
        ("1.4.1", "get a pet", "GET"),
        ("1.4.2", "update a pet", "POST"),
        ("2", None, "webhooks"),
        ("2.1", None, "orderCreated"),
        ("2.1.1", "order created", "POST"),
    ]
    assert [node.path for node in tree.indexed() if node.key in {"GET", "QUERY", "COPY", "POST"}] == [
        "pets/GET",
        "pets/QUERY",
        "pets/COPY",
        "pets/{petId}/GET",
        "pets/{petId}/POST",
        "webhooks/orderCreated/POST",
    ]
    assert tree.resolve("webhooks/orderCreated/POST").description == "order created"


def test_openapi_viewer_indexes_structural_prefixes(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        "openapi: 3.2.1\npaths:\n  /pets/{petId}:\n    get:\n      summary: Get a pet\n",
        encoding="utf-8",
    )

    tree = OpenapiViewer().build(content, cache_metadata("openapi", content_name="openapi.yaml"))
    selected = tree.select("pets")

    assert [(node.index, node.path, node.node_type) for node in selected] == [
        ("1", "pets/{petId}", "ordinary"),
        ("1.1", "pets/{petId}/GET", "leaf"),
    ]
    with pytest.raises(ProjectionError) as caught:
        tree.select("pets/{petId}/DELETE")
    assert caught.value.values["prefix"] == "pets/{petId}"
    assert caught.value.values["nodes"] == [
        {"index": "1", "key": "GET", "node_type": "leaf", "description": "Get a pet"}
    ]


def test_openapi_viewer_rejects_a_path_and_method_key_collision(
    tmp_path: Path,
    document: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(document("openapi/viewers/key-collision.yaml"), encoding="utf-8")

    with pytest.raises(ProjectionError) as caught:
        OpenapiViewer().build(content, cache_metadata("openapi", content_name="openapi.yaml"))

    assert caught.value.reason_code == ProjectionReason.DUPLICATE_KEY
    assert caught.value.values == {"key": "GET"}
