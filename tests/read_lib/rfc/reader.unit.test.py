# tests/read_lib/rfc/reader.unit.test.py
from collections.abc import Callable
from pathlib import Path

from apiscope.cache import CacheMetadata
from apiscope.read_lib.rfc.reader import RfcReader
from apiscope.view_lib.schema import IndexedNode


def test_rfc_reader_returns_an_xml_section(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><front><title>Example</title></front><middle><section anchor="scope">'
        "<name>Scope</name><t>Keep this paragraph.</t></section></middle></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(content, cache_metadata("rfc", content_name="rfc.xml"), indexed_node("scope"))

    assert result.target == "scope"
    assert result.kind == "text"
    assert result.media_type == "application/rfc+xml"
    assert result.content == '<section anchor="scope"><name>Scope</name><t>Keep this paragraph.</t></section>'


def test_rfc_reader_returns_the_xml_overview(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        "<rfc><front><title>Example</title><abstract><t>Summary.</t></abstract></front></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(content, cache_metadata("rfc", content_name="rfc.xml"), indexed_node("overview"))

    assert result.content == "<front><title>Example</title><abstract><t>Summary.</t></abstract></front>"


def test_rfc_reader_returns_one_xml_reference(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references title="Normative References"><reference anchor="RFC2119">'
        "<front><title>Key words for use in RFCs</title></front>"
        "</reference></references></back></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(
        content,
        cache_metadata("rfc", content_name="rfc.xml"),
        indexed_node("references/RFC2119", key="RFC2119"),
    )

    assert result.content == (
        '<reference anchor="RFC2119"><front><title>Key words for use in RFCs</title></front></reference>'
    )


def test_rfc_reader_resolves_a_reference_group_without_a_title(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.xml").write_text(
        '<rfc><back><references><reference anchor="RFC2119">'
        "<front><title>Key words for use in RFCs</title></front>"
        "</reference></references></back></rfc>",
        encoding="utf-8",
    )

    result = RfcReader().read(
        content,
        cache_metadata("rfc", content_name="rfc.xml"),
        indexed_node("references/RFC2119", key="RFC2119"),
    )

    assert result.content is not None
    assert "<title>Key words for use in RFCs</title>" in result.content


def test_rfc_reader_returns_one_text_page(
    tmp_path: Path,
    cache_metadata: Callable[..., CacheMetadata],
    indexed_node: Callable[..., IndexedNode],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "rfc.txt").write_text("cover\fcontents\fbody page\n", encoding="utf-8")

    result = RfcReader().read(content, cache_metadata("rfc", content_name="rfc.txt"), indexed_node("page/2"))

    assert result.content == "contents"
    assert result.media_type == "text/plain"
    assert result.size == len(b"contents")
