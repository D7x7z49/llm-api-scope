# apiscope/sync/_lib/llmstxt/markdown.py
# resolve the markdown sibling a page may serve, per the llms.txt proposal.
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

_MARKDOWN_SUFFIXES = (".md", ".markdown")
_HTML_PREFIXES = (b"<!doctype", b"<html")


# the proposal offers two forms: replace the extension, or append .md.
# a url without a file name uses an index file, but github serves page.md.
def markdown_candidates(target: str) -> list[str]:
    path = urlsplit(target).path
    if path.lower().endswith(_MARKDOWN_SUFFIXES):
        return []
    name = path.rpartition("/")[2]
    base = path.rstrip("/")
    candidates: list[str] = []
    if "." in name:
        candidates.append(_with_path(target, f"{path[: path.rfind('.')]}.md"))
        candidates.append(_with_path(target, f"{path}.md"))
    else:
        if base:
            candidates.append(_with_path(target, f"{base}.md"))
        candidates.append(_with_path(target, f"{base}/index.md"))
        candidates.append(_with_path(target, f"{base}/index.html.md"))
    return list(dict.fromkeys(candidates))


# a candidate that answers an html shell is not the markdown version.
def is_html(data: bytes) -> bool:
    head = data.lstrip()[:16].lower()
    return head.startswith(_HTML_PREFIXES)


def _with_path(target: str, path: str) -> str:
    parts = urlsplit(target)
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))
