# tests/read_lib/openapi/reader.unit.test.py
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from apiscope.cache import CacheMetadata
from apiscope.read_lib.errors import ReadError
from apiscope.read_lib.openapi.reader import OpenapiReader
from apiscope.view_lib.schema import IndexedNode


def test_openapi_reader_reads_one_operation_and_keeps_path_item_context(
    tmp_path: Path,
    document: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        document("openapi/readers/list-pets-path-item.yaml"),
        encoding="utf-8",
    )

    result = OpenapiReader().read(
        content,
        cache_metadata("openapi", content_name="openapi.yaml"),
        indexed_node("/pets/GET", key="GET"),
    )

    assert result.target == "/pets/GET"
    assert result.kind == "text"
    assert result.content is not None
    assert yaml.safe_load(result.content) == {
        "summary": "Pet collection",
        "parameters": [{"name": "limit"}],
        "get": {"$ref": "#/components/operations/ListPets"},
    }
    assert result.media_type == "application/yaml"
    assert result.encoding == "utf-8"
    assert result.size == len(result.content.encode("utf-8"))


def test_openapi_reader_reads_a_webhook_operation(
    tmp_path: Path,
    document: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        document("openapi/readers/webhook.yaml"),
        encoding="utf-8",
    )

    result = OpenapiReader().read(
        content,
        cache_metadata("openapi", content_name="openapi.yaml"),
        indexed_node("webhooks/orderCreated/POST", key="POST"),
    )

    assert result.target == "webhooks/orderCreated/POST"
    assert result.content is not None
    assert yaml.safe_load(result.content) == {"post": {"summary": "Notify the consumer"}}


def test_openapi_reader_reports_a_missing_operation(
    tmp_path: Path,
    document: Callable[[str], str],
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        document("openapi/readers/list-pets.yaml"),
        encoding="utf-8",
    )

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_found"):
        OpenapiReader().read(
            content,
            cache_metadata("openapi", content_name="openapi.yaml"),
            indexed_node("/pets/DELETE", key="DELETE"),
        )


def test_openapi_reader_reports_a_missing_path(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text("openapi: 3.2.1\npaths: {}\n", encoding="utf-8")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.target_not_found"):
        OpenapiReader().read(
            content,
            cache_metadata("openapi", content_name="openapi.yaml"),
            indexed_node("/missing/GET", key="GET"),
        )


@pytest.mark.parametrize("document_text", ["[", "openapi: 3.2.1\npaths: []\n"], ids=["bad-yaml", "paths-not-map"])
def test_openapi_reader_rejects_invalid_documents(
    tmp_path: Path,
    document_text: str,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(document_text, encoding="utf-8")

    with pytest.raises(ReadError, match=r"read_lib\.reader\.content_invalid"):
        OpenapiReader().read(
            content,
            cache_metadata("openapi", content_name="openapi.yaml"),
            indexed_node("/pets/GET", key="GET"),
        )
