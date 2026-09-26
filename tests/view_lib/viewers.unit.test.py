# tests/view_lib/viewers.unit.test.py
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata, ContentKind
from apiscope.schema import DocumentType
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError
from apiscope.view_lib.filesystem.viewer import FilesystemViewer
from apiscope.view_lib.llmstxt.viewer import LlmstxtViewer
from apiscope.view_lib.openapi.viewer import OpenapiViewer
from apiscope.view_lib.repo.viewer import RepoViewer
from apiscope.view_lib.rfc.viewer import RfcViewer


def _metadata(doc_type: DocumentType, *, kind: ContentKind = "file", name: str | None = "document") -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type=doc_type,
        source="test-source",
        fetched_at=datetime.now(timezone.utc),
        content_kind=kind,
        content_name=name,
        content_digest="digest",
    )


def test_filesystem_viewer_builds_a_sorted_directory_tree(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "z").mkdir(parents=True)
    (content / "a").mkdir()
    (content / "z" / "last.md").write_text("", encoding="utf-8")
    (content / "a" / "first.md").write_text("", encoding="utf-8")

    tree = FilesystemViewer().build(content, _metadata("filesystem", kind="directory", name=None))

    assert [(node.index, node.value) for node in tree.indexed()] == [
        ("1", "a"),
        ("1.1", "first.md"),
        ("2", "z"),
        ("2.1", "last.md"),
    ]
    assert tree.resolve_index("1").node_type == "ordinary"
    assert tree.resolve_index("1.1").node_type == "leaf"


def test_filesystem_viewer_keeps_empty_directories_ordinary(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "empty").mkdir(parents=True)

    tree = FilesystemViewer().build(content, _metadata("filesystem", kind="directory", name=None))

    assert tree.resolve_index("1").node_type == "ordinary"


def test_repo_viewer_hides_git_metadata(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / ".git").mkdir(parents=True)
    (content / ".git" / "config").write_text("", encoding="utf-8")
    (content / "README.md").write_text("", encoding="utf-8")

    tree = RepoViewer().build(content, _metadata("repo", kind="directory", name=None))

    assert [node.value for node in tree.indexed()] == ["README.md"]


def test_openapi_viewer_keeps_path_hints_and_method_order(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        """
openapi: 3.2.1
paths:
  /pets/{petId}:
    summary: one pet
    post:
      summary: update a pet
    get:
      summary: get a pet
  /pets:
    summary: pet collection
    get:
      summary: list pets
    query:
      summary: query pets
    additionalOperations:
      COPY:
        summary: copy pets
webhooks:
  orderCreated:
    post:
      summary: order created
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = OpenapiViewer().build(content, _metadata("openapi", name="openapi.yaml"))

    assert tree.select("pets/")[0].path == "/pets"
    assert [(node.index, node.value, node.key) for node in tree.indexed()] == [
        ("1", "pet collection", "/pets"),
        ("1.1", "list pets", "GET"),
        ("1.2", "query pets", "QUERY"),
        ("1.3", "copy pets", "COPY"),
        ("1.4", "one pet", "{petId}"),
        ("1.4.1", "get a pet", "GET"),
        ("1.4.2", "update a pet", "POST"),
        ("2", "webhooks", None),
        ("2.1", "orderCreated", None),
        ("2.1.1", "order created", "POST"),
    ]
    assert [node.path for node in tree.indexed() if node.key in {"GET", "QUERY", "COPY", "POST"}] == [
        "/pets/GET",
        "/pets/QUERY",
        "/pets/COPY",
        "/pets/{petId}/GET",
        "/pets/{petId}/POST",
        "webhooks/orderCreated/POST",
    ]
    assert tree.resolve("webhooks/orderCreated/POST").value == "order created"


def test_openapi_viewer_indexes_structural_prefixes(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        "openapi: 3.2.1\npaths:\n  /pets/{petId}:\n    get:\n      summary: Get a pet\n",
        encoding="utf-8",
    )

    tree = OpenapiViewer().build(content, _metadata("openapi", name="openapi.yaml"))
    selected = tree.select("pets")

    assert [(node.index, node.path, node.node_type) for node in selected] == [
        ("1", "/pets", "ordinary"),
        ("1.1", "/pets/{petId}", "ordinary"),
        ("1.1.1", "/pets/{petId}/GET", "leaf"),
    ]
    with pytest.raises(ProjectionError) as caught:
        tree.select("pets/{petId}/DELETE")
    assert caught.value.values["prefix"] == "/pets/{petId}"
    assert caught.value.values["routes"] == [{"index": "1.1.1", "route": "/pets/{petId}/GET", "label": "GET"}]


def test_openapi_viewer_preserves_path_and_method_route_collisions(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "openapi.yaml").write_text(
        """
openapi: 3.2.1
paths:
  /pets:
    get:
      summary: List pets
  /pets/GET:
    post:
      summary: Create a GET-named pet resource
""".lstrip(),
        encoding="utf-8",
    )

    tree = OpenapiViewer().build(content, _metadata("openapi", name="openapi.yaml"))

    with pytest.raises(ProjectionError) as caught:
        tree.select("pets/GET")
    assert caught.value.reason_code == ProjectionReason.PATH_AMBIGUOUS
    assert caught.value.values["routes"] == [
        {"index": "1.1", "route": "/pets/GET", "label": "GET", "node_type": "leaf"},
        {"index": "1.2", "route": "/pets/GET", "label": "GET", "node_type": "ordinary"},
    ]


def test_rfc_viewer_accepts_numbered_and_unnumbered_sections(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.txt").write_text(
        """
RFC example

1. Introduction
1.1. Scope
Security Considerations
Normative References

[RFC2119] Key words for use in RFCs.
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, _metadata("rfc", name="rfc.txt"))

    assert [(node.index, node.value, node.key) for node in tree.indexed()] == [
        ("1", "Overview", None),
        ("2", "1. Introduction", None),
        ("2.1", "1.1. Scope", None),
        ("3", "Security Considerations", None),
        ("4", "Normative References", None),
        ("4.1", "Key words for use in RFCs.", "RFC2119"),
    ]


def test_llmstxt_viewer_keeps_links_as_key_value_leaves(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text(
        """
# Project
> A short summary.

## Documentation
- [Getting Started](https://example.test/start.md): Install the project.
- [API Reference](https://example.test/api.md)

## Optional
- [Migration](https://example.test/migrate.md)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = LlmstxtViewer().build(content, _metadata("llmstxt", name="llms.txt"))

    assert [(node.index, node.value, node.key) for node in tree.indexed()] == [
        ("1", "Overview", None),
        ("2", "Documentation", None),
        ("2.1", "https://example.test/start.md — Install the project.", "Getting Started"),
        ("2.2", "https://example.test/api.md", "API Reference"),
        ("3", "Optional", None),
        ("3.1", "https://example.test/migrate.md", "Migration"),
    ]
