# apiscope/view_lib/hint.py
from __future__ import annotations

from collections.abc import Iterable, Mapping


def render_route_hint(address: str, nodes: Iterable[Mapping[str, object]]) -> str:
    lines = [address]
    for node in nodes:
        mark = "[*]" if node.get("node_type") == "leaf" else "[/]"
        description = node.get("description")
        suffix = f": {description}" if description else ""
        lines.append(f"- {mark}[{node.get('index')}] {node.get('key')}{suffix}")
    return "\n".join(lines)
