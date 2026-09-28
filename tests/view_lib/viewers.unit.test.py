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


def _metadata(
    doc_type: DocumentType,
    *,
    kind: ContentKind = "file",
    name: str | None = "document",
    source: str = "test-source",
) -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type=doc_type,
        source=source,
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

    assert [(node.index, node.key) for node in tree.indexed()] == [
        ("1", "a"),
        ("1.1", "first.md"),
        ("2", "z"),
        ("2.1", "last.md"),
    ]
    nodes = {node.index: node for node in tree.indexed()}
    assert nodes["1"].node_type == "ordinary"
    assert nodes["1.1"].node_type == "leaf"


def test_filesystem_viewer_keeps_empty_directories_ordinary(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "empty").mkdir(parents=True)

    tree = FilesystemViewer().build(content, _metadata("filesystem", kind="directory", name=None))

    assert tree.indexed()[0].node_type == "ordinary"


def test_filesystem_viewer_does_not_follow_a_self_link(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "readme.md").write_text("", encoding="utf-8")
    (content / "self").symlink_to(content)

    tree = FilesystemViewer().build(content, _metadata("filesystem", kind="directory", name=None))

    assert [(node.index, node.key, node.node_type) for node in tree.indexed()] == [
        ("1", "readme.md", "leaf"),
        ("2", "self", "leaf"),
    ]


def test_filesystem_viewer_marks_an_outside_link_as_a_leaf(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("", encoding="utf-8")
    content = tmp_path / "content"
    content.mkdir()
    (content / "link").symlink_to(outside)

    tree = FilesystemViewer().build(content, _metadata("filesystem", kind="directory", name=None))

    assert [(node.index, node.key, node.node_type) for node in tree.indexed()] == [("1", "link", "leaf")]


def test_repo_viewer_hides_git_metadata(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / ".git").mkdir(parents=True)
    (content / ".git" / "config").write_text("", encoding="utf-8")
    (content / "README.md").write_text("", encoding="utf-8")

    tree = RepoViewer().build(content, _metadata("repo", kind="directory", name=None))

    assert [node.key for node in tree.indexed()] == ["README.md"]


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

    assert tree.select("pets/")[0].path == "pets"
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
        ("1", "pets", "ordinary"),
        ("1.1", "pets/{petId}", "ordinary"),
        ("1.1.1", "pets/{petId}/GET", "leaf"),
    ]
    with pytest.raises(ProjectionError) as caught:
        tree.select("pets/{petId}/DELETE")
    assert caught.value.values["prefix"] == "pets/{petId}"
    assert caught.value.values["nodes"] == [
        {"index": "1", "key": "GET", "node_type": "leaf", "description": "Get a pet"}
    ]


def test_openapi_viewer_rejects_a_path_and_method_key_collision(tmp_path: Path) -> None:
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

    with pytest.raises(ProjectionError) as caught:
        OpenapiViewer().build(content, _metadata("openapi", name="openapi.yaml"))

    assert caught.value.reason_code == ProjectionReason.DUPLICATE_KEY
    assert caught.value.values == {"key": "GET"}


def test_rfc_viewer_uses_a_stable_route_for_untitled_reference_groups(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references><reference anchor="RFC2119"><front>'
        "<title>Key words for use in RFCs</title></front></reference></references></back></rfc>",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, _metadata("rfc", name="rfc.xml"))

    group = tree.resolve("references")
    reference = tree.resolve("references/RFC2119")
    assert group.key == "references"
    assert reference.description == "Key words for use in RFCs"


def test_rfc_viewer_uses_pn_numbers_relative_to_the_parent(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        "<rfc><middle>"
        '<section pn="section-3"><name>Dynamic Subscriptions</name>'
        '<section pn="section-3.1"><name>Transport Connectivity</name></section></section>'
        "</middle><back>"
        '<references pn="section-10"><name>References</name>'
        '<references pn="section-10.1"><name>Normative References</name>'
        '<reference anchor="RFC2119" pn="section-10.1.1"><front>'
        "<title>Key words</title></front></reference></references></references>"
        "</back></rfc>",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, _metadata("rfc", name="rfc.xml"))

    assert [(node.index, node.key, node.path) for node in tree.indexed()] == [
        ("1", "overview", "overview"),
        ("2", "3", "3"),
        ("2.1", "1", "3/1"),
        ("3", "10", "10"),
        ("3.1", "1", "10/1"),
        ("3.1.1", "RFC2119", "10/1/RFC2119"),
    ]


def test_rfc_viewer_indexes_txt_pages_at_form_feed_boundaries(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.txt").write_text("cover\fcontents\f1. Introduction\nbody\n", encoding="utf-8")

    tree = RfcViewer().build(content, _metadata("rfc", name="rfc.txt"))

    assert [(node.index, node.key, node.path, node.node_type) for node in tree.indexed()] == [
        ("1", "page", "page", "ordinary"),
        ("1.1", "1", "page/1", "leaf"),
        ("1.2", "2", "page/2", "leaf"),
        ("1.3", "3", "page/3", "leaf"),
    ]


def test_rfc_viewer_keeps_xml_section_anchors(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><front><title>Example</title></front><middle><section anchor="intro">'
        '<name>Introduction</name><section anchor="scope"><name>Scope</name></section>'
        "</section></middle></rfc>",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, _metadata("rfc", name="rfc.xml"))

    assert [(node.index, node.path, node.node_type) for node in tree.indexed()] == [
        ("1", "overview", "leaf"),
        ("2", "intro", "ordinary"),
        ("2.1", "intro/scope", "leaf"),
    ]


def test_llmstxt_viewer_builds_routes_from_link_urls(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text(
        """
# Project
> A short summary.

## Documentation
- [Getting Started](https://example.test/docs/guides/start.md): Install the project.
- [API Reference](https://example.test/docs/reference/api.md)
- [Catalog](https://example.test/docs/catalog.json)

## External
- [Help](https://other.test/help.md)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = LlmstxtViewer().build(
        content,
        _metadata("llmstxt", name="llms.txt", source="https://example.test/docs/llms.txt"),
    )

    assert [(node.index, node.path, node.node_type) for node in tree.indexed()] == [
        ("1", "overview", "leaf"),
        ("2", "catalog.json", "leaf"),
        ("3", "guides", "ordinary"),
        ("3.1", "guides/start.md", "leaf"),
        ("4", "other.test", "ordinary"),
        ("4.1", "other.test/help.md", "leaf"),
        ("5", "reference", "ordinary"),
        ("5.1", "reference/api.md", "leaf"),
    ]
    node = tree.resolve("guides/start.md")
    assert node.key == "start.md"
    assert node.description == "[Getting Started] Install the project."
    assert node.source_target == "https://example.test/docs/guides/start.md"


def test_llmstxt_viewer_resolves_relative_links_from_a_nested_index(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text(
        "# Pydantic\n\n## Get Started\n- [Install](get-started/install/index.md)\n",
        encoding="utf-8",
    )

    tree = LlmstxtViewer().build(
        content,
        _metadata(
            "llmstxt",
            name="llms.txt",
            source="https://pydantic.dev/docs/validation/latest/llms.txt",
        ),
    )

    node = tree.resolve("get-started/install/index.md")
    assert node.source_target == "https://pydantic.dev/docs/validation/latest/get-started/install/index.md"


def test_llmstxt_viewer_strips_a_local_source_directory(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text(
        "# Docs\n\n## Guides\n- [Install](install.md): Install the project.\n- [Reference](api/reference.md)\n",
        encoding="utf-8",
    )

    tree = LlmstxtViewer().build(
        content,
        _metadata("llmstxt", name="llms.txt", source=str(content / "llms.txt")),
    )

    assert [(node.index, node.key, node.path) for node in tree.indexed()] == [
        ("1", "Overview", "overview"),
        ("2", "api", "api"),
        ("2.1", "reference.md", "api/reference.md"),
        ("3", "install.md", "install.md"),
    ]


def test_llmstxt_viewer_deduplicates_a_repeated_url(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "llms.txt").write_text(
        """# Docs

## One
- [First](https://example.test/docs/guide.md)
- [Second](https://example.test/docs/guide.md)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    tree = LlmstxtViewer().build(
        content,
        _metadata("llmstxt", name="llms.txt", source="https://example.test/docs/llms.txt"),
    )

    assert [(node.index, node.key, node.path) for node in tree.indexed()] == [
        ("1", "Overview", "overview"),
        ("2", "guide.md", "guide.md"),
    ]
    assert tree.resolve("guide.md").description == "[First]"
