# tests/rfc/parse_xml.unit.test.py

import pytest

from apiscope.rfc.parse_xml import parse_xml_section, parse_xml_toc

XML = """\
<?xml version='1.0' encoding='utf-8'?>
<rfc>
  <middle>
    <section pn="section-1">
      <name>Introduction</name>
      <t>Text.</t>
    </section>
    <section pn="section-2">
      <name>Protocol</name>
      <section pn="section-2.1">
        <name>Header</name>
        <t>First.</t>
        <t>Second.</t>
      </section>
    </section>
  </middle>
  <back>
    <section pn="section-appendix.a">
      <name>Examples</name>
      <t>Example.</t>
    </section>
  </back>
</rfc>
"""

XML_EMPTY = """\
<?xml version='1.0' encoding='utf-8'?>
<rfc><middle></middle></rfc>
"""

XML_TOC_EXCLUDE = """\
<?xml version='1.0' encoding='utf-8'?>
<rfc><middle>
    <section pn="section-skip" toc="exclude"><name>Skip</name><t>x</t></section>
    <section pn="section-keep"><name>Keep</name><t>x</t></section>
</middle></rfc>
"""


@pytest.fixture
def toc():
    return parse_xml_toc(XML)


def test_toc_empty_middle_and_back():
    root = parse_xml_toc(XML_EMPTY)
    assert root.children == []


def test_toc_normalizes_section_ids(toc):
    ids = [e.id for e in toc.children]
    assert ids == ["1", "2", "a"]


def test_toc_nested_children(toc):
    s2 = toc.children[1]
    assert len(s2.children) == 1
    assert s2.children[0].id == "2.1"


def test_toc_excludes_toc_exclude():
    root = parse_xml_toc(XML_TOC_EXCLUDE)
    assert len(root.children) == 1


def test_section_leaf_has_content():
    node = parse_xml_section(XML, "1")
    assert node.content is not None
    assert node.children == []


def test_section_internal_has_children():
    node = parse_xml_section(XML, "2")
    assert node.content is None
    assert len(node.children) == 1


def test_section_not_found_raises():
    with pytest.raises(ValueError, match="not found"):
        parse_xml_section(XML, "99")
