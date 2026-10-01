# apiscope/view_lib/rfc/xml.py
from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from typing import Literal

RfcNodeKind = Literal["overview", "section", "references", "reference"]


class RfcXmlError(Exception):
    pass


@dataclass(slots=True)
class RfcNode:
    route: str
    key: str
    element: ElementTree.Element
    kind: RfcNodeKind
    description: str | None = None
    children: tuple[RfcNode, ...] = field(default_factory=tuple)


def parse_rfc_xml(raw: bytes) -> tuple[RfcNode, ...]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise RfcXmlError("rfc xml is not well formed") from error
    if _local_name(root.tag) != "rfc":
        raise RfcXmlError("root element is not rfc")

    front = _child(root, "front")
    nodes: list[RfcNode] = [
        RfcNode(route="overview", key="overview", element=front if front is not None else root, kind="overview"),
    ]
    middle = _child(root, "middle")
    if middle is not None:
        for section in _children(middle, "section"):
            nodes.append(_section_node(section, route="", parent_number=None))
    back = _child(root, "back")
    if back is not None:
        for references in _children(back, "references"):
            nodes.append(_references_node(references, route="", parent_number=None))
    return tuple(nodes)


def _section_node(element: ElementTree.Element, *, route: str, parent_number: str | None) -> RfcNode:
    title = _element_text(_child(element, "name")) or _element_text(_child(element, "title"))
    number = _pn_number(element)
    key = _relative_key(number, parent_number) if number else (element.attrib.get("anchor") or "section")
    current_route = _join(route, key)
    children = tuple(
        _section_node(child, route=current_route, parent_number=number) for child in _children(element, "section")
    )
    return RfcNode(
        route=current_route,
        key=key,
        element=element,
        kind="section",
        description=title or None,
        children=children,
    )


def _references_node(element: ElementTree.Element, *, route: str, parent_number: str | None) -> RfcNode:
    title = _element_text(_child(element, "name")) or element.attrib.get("title")
    number = _pn_number(element)
    key = _relative_key(number, parent_number) if number else (element.attrib.get("anchor") or "references")
    current_route = _join(route, key)
    children: list[RfcNode] = []
    for child in element:
        name = _local_name(child.tag)
        if name == "references":
            children.append(_references_node(child, route=current_route, parent_number=number))
        elif name == "reference":
            children.append(_reference_node(child, route=current_route))
    return RfcNode(
        route=current_route,
        key=key,
        element=element,
        kind="references",
        description=title or None,
        children=tuple(children),
    )


def _reference_node(element: ElementTree.Element, *, route: str) -> RfcNode:
    number = _pn_number(element)
    number_key = _relative_key(number, None) if number else None
    key = element.attrib.get("anchor") or element.attrib.get("target") or number_key or "reference"
    front = _child(element, "front")
    title = _element_text(_child(front, "title")) if front is not None else ""
    return RfcNode(
        route=_join(route, key),
        key=key,
        element=element,
        kind="reference",
        description=title or None,
    )


def _pn_number(element: ElementTree.Element) -> str | None:
    pn = element.attrib.get("pn")
    if not pn:
        return None
    prefix = "section-"
    return pn[len(prefix) :] if pn.startswith(prefix) else pn


def _relative_key(number: str, parent_number: str | None) -> str:
    if parent_number and number.startswith(f"{parent_number}."):
        return number[len(parent_number) + 1 :]
    return number


def _join(route: str, key: str) -> str:
    return key if not route else f"{route}/{key}"


def _child(element: ElementTree.Element | None, name: str) -> ElementTree.Element | None:
    if element is None:
        return None
    return next((child for child in element if _local_name(child.tag) == name), None)


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _element_text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
