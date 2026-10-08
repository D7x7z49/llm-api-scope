# tests/view_lib/rfc/viewer.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.view_lib.rfc.viewer import RfcViewer


def test_rfc_viewer_uses_a_stable_route_for_untitled_reference_groups(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references><reference anchor="RFC2119"><front>'
        "<title>Key words for use in RFCs</title></front></reference></references></back></rfc>",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, cache_metadata("rfc", content_name="rfc.xml"))

    group = tree.resolve("references")
    reference = tree.resolve("references/RFC2119")
    assert group.key == "references"
    assert reference.description == "Key words for use in RFCs"


def test_rfc_viewer_uses_pn_numbers_relative_to_the_parent(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
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

    tree = RfcViewer().build(content, cache_metadata("rfc", content_name="rfc.xml"))

    assert [(node.index, node.key, node.path) for node in tree.indexed()] == [
        ("1", "overview", "overview"),
        ("2", "3", "3"),
        ("2.1", "1", "3/1"),
        ("3", "10", "10"),
        ("3.1", "1", "10/1"),
        ("3.1.1", "RFC2119", "10/1/RFC2119"),
    ]


def test_rfc_viewer_indexes_txt_pages_at_form_feed_boundaries(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.txt").write_text("cover\fcontents\f1. Introduction\nbody\n", encoding="utf-8")

    tree = RfcViewer().build(content, cache_metadata("rfc", content_name="rfc.txt"))

    assert [(node.index, node.key, node.path, node.node_type) for node in tree.indexed()] == [
        ("1", "page", "page", "ordinary"),
        ("1.1", "1", "page/1", "leaf"),
        ("1.2", "2", "page/2", "leaf"),
        ("1.3", "3", "page/3", "leaf"),
    ]


def test_rfc_viewer_keeps_xml_section_anchors(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><front><title>Example</title></front><middle><section anchor="intro">'
        '<name>Introduction</name><section anchor="scope"><name>Scope</name></section>'
        "</section></middle></rfc>",
        encoding="utf-8",
    )

    tree = RfcViewer().build(content, cache_metadata("rfc", content_name="rfc.xml"))

    assert [(node.index, node.path, node.node_type) for node in tree.indexed()] == [
        ("1", "overview", "leaf"),
        ("2", "intro", "ordinary"),
        ("2.1", "intro/scope", "leaf"),
    ]
