# tests/view_lib/viewers.unit.test.py
from datetime import datetime, timezone
from pathlib import Path

from apiscope.cache import CacheMetadata, ContentKind
from apiscope.schema import DocumentType
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
openapi: 3.1.0
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
webhooks:
  orderCreated:
    post:
      summary: order created
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = OpenapiViewer().build(content, _metadata("openapi", name="openapi.yaml"))

    assert [(node.index, node.value, node.key) for node in tree.indexed()] == [
        ("1", "pet collection", "/pets"),
        ("1.1", "list pets", "GET"),
        ("1.2", "one pet", "{petId}"),
        ("1.2.1", "get a pet", "GET"),
        ("1.2.2", "update a pet", "POST"),
        ("2", "webhooks", None),
        ("2.1", "orderCreated", None),
        ("2.1.1", "order created", "POST"),
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
