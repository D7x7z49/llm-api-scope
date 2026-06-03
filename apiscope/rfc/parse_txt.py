# apiscope/rfc/parse_txt.py

from __future__ import annotations

import re

PAGE_RE = re.compile(r"\[Page (\d+)\]")


# ==============================================================================
# public api
# ==============================================================================


def page_count(content: str) -> int:
    matches = PAGE_RE.findall(content)
    return int(matches[-1]) if matches else 1


def split_pages(content: str) -> list[tuple[int, int, int]]:
    # returns [(page_number, start_line, end_line), ...]
    lines = content.split("\n")
    boundaries: list[tuple[int, int]] = []  # [(page, line_index), ...]

    for i, line in enumerate(lines):
        m = PAGE_RE.search(line)
        if m:
            boundaries.append((int(m.group(1)), i))

    if not boundaries:
        return [(1, 0, len(lines))]

    result: list[tuple[int, int, int]] = []
    for idx, (page_num, line_num) in enumerate(boundaries):
        start = 0 if idx == 0 else boundaries[idx - 1][1] + 1
        end = line_num + 1
        result.append((page_num, start, end))

    # last page from last marker to EOF
    last_end = boundaries[-1][1] + 1
    if last_end < len(lines):
        # assume next sequential page
        next_page = boundaries[-1][0] + 1
        result.append((next_page, last_end, len(lines)))

    return result


def extract_page(content: str, page: int) -> str:
    pages = split_pages(content)
    for p, start, end in pages:
        if p == page:
            return "\n".join(content.split("\n")[start:end])
    raise ValueError(f"page {page} not found")
