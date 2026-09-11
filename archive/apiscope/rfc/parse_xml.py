# apiscope/rfc/parse_xml.py

from __future__ import annotations

import xml.etree.ElementTree as ET

from pydantic import BaseModel


class TocEntry(BaseModel):
    # normalized section id: "3.5.1" "a.1" etc.
    id: str
    title: str
    # non-None = leaf node with body text, children empty
    # None = internal node, see children
    content: str | None = None
    children: list[TocEntry] = []


# ==============================================================================
# helpers
# ==============================================================================


def _pn_to_id(pn: str) -> str:
    # pn = xml attribute: "section-3.5.1" "section-appendix.a.1"
    if pn.startswith("section-appendix."):
        return pn.replace("section-appendix.", "", 1)
    if pn.startswith("section-"):
        return pn.replace("section-", "", 1)
    return pn


# ==============================================================================
# public api
# ==============================================================================


def parse_xml_toc(content: str) -> TocEntry:
    tree = ET.fromstring(content)
    children: list[TocEntry] = []

    for parent_tag in ("middle", "back"):
        parent = tree.find(parent_tag)
        if parent is not None:
            _collect_xml_toc(parent.findall("section"), children)

    return TocEntry(id="", title="", children=children)


def _collect_xml_toc(sections: list[ET.Element], entries: list[TocEntry]) -> None:
    for section in sections:
        if section.get("toc") == "exclude":
            continue

        pn = section.get("pn", "")
        section_id = _pn_to_id(pn)
        name_elem = section.find("name")
        title = "".join(name_elem.itertext()).strip() if name_elem is not None else ""

        child_sections = section.findall("section")
        children: list[TocEntry] = []
        if child_sections:
            _collect_xml_toc(child_sections, children)

        entries.append(TocEntry(id=section_id, title=title, children=children))


def parse_xml_section(content: str, section_id: str) -> TocEntry:
    tree = ET.fromstring(content)

    pn = f"section-{section_id}"
    section = tree.find(f".//*[@pn='{pn}']")
    if section is None:
        raise ValueError(f"section '{section_id}' not found")

    name_elem = section.find("name")
    title = "".join(name_elem.itertext()).strip() if name_elem is not None else ""

    child_sections = section.findall("section")
    if child_sections:
        children: list[TocEntry] = []
        _collect_xml_toc(child_sections, children)
        return TocEntry(id=section_id, title=title, children=children)

    # leaf: collect text from <t> elements
    texts: list[str] = []
    for t in section.iter("t"):
        text = "".join(t.itertext()).strip()
        if text:
            texts.append(text)
    body = "\n\n".join(texts)
    return TocEntry(id=section_id, title=title, content=body)
