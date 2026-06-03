# apiscope/rfc/search.py

from __future__ import annotations

from difflib import SequenceMatcher

from apiscope.rfc.parse_txt import split_pages


def match_trigram(text: str, keyword: str, threshold: float = 0.7) -> bool:
    # check if keyword appears in text via trigram similarity
    text_lower = text.lower()
    kw_lower = keyword.lower()

    if not kw_lower:
        return False

    if kw_lower in text_lower:
        return True

    # word-level fuzzy match for typos
    for word in text_lower.split():
        if len(word) < 3:
            continue
        if SequenceMatcher(None, kw_lower, word).ratio() >= threshold:
            return True

    return False


def search_content(content: str, keyword: str, context: int = 1) -> list[tuple[int, str]]:
    pages = split_pages(content)
    lines = content.split("\n")
    kw_lower = keyword.lower()
    results: list[tuple[int, str]] = []

    for page, start, end in pages:
        page_lines = lines[start:end]
        match_idx = -1

        for i, line in enumerate(page_lines):
            stripped = line.strip("\x0c").strip()
            if kw_lower in stripped.lower():
                match_idx = i
                break

        if match_idx < 0:
            continue

        # extract context lines
        ctx_start = max(0, match_idx - context)
        ctx_end = min(len(page_lines), match_idx + context + 1)
        snippet_lines = page_lines[ctx_start:ctx_end]

        # strip form feed characters from snippet
        snippet = "\n".join(snippet_lines).replace("\x0c", "").strip()
        if snippet:
            results.append((page, snippet))

    return results
