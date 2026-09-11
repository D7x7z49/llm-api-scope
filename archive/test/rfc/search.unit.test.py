# tests/rfc/search.unit.test.py

from apiscope.rfc.search import match_trigram, search_content

TXT_CONTENT = """
[Page 1]

RFC Title

1. Introduction

   This document specifies the Internet Protocol.

2. Overview

   The protocol provides end-to-end connectivity.

[Page 2]

3. Details

   Packet format includes header fields.

4. Security

   Security considerations are discussed.
"""


def test_match_trigram_empty_keyword():
    assert match_trigram("any text", "") is False


def test_match_trigram_exact_substring():
    assert match_trigram("hello world", "world") is True


def test_match_trigram_fuzzy_word():
    assert match_trigram("protocol specification", "protcol") is True


def test_match_trigram_no_match():
    assert match_trigram("network layer", "transport") is False


def test_search_content_finds_match():
    results = search_content(TXT_CONTENT, "Internet")
    assert len(results) == 1
    assert results[0][0] == 2  # [Page 1] marker itself is page 1


def test_search_content_multiple_pages():
    results = search_content(TXT_CONTENT, "con")
    # "connectivity" on page 2, "considerations" on page 3
    assert len(results) == 2
    pages = {p for p, _ in results}
    assert pages == {2, 3}


def test_search_content_no_match():
    results = search_content(TXT_CONTENT, "quantum")
    assert results == []


def test_search_content_context_lines():
    results = search_content(TXT_CONTENT, "Packet", context=2)
    assert len(results) == 1
    page, snippet = results[0]
    assert page == 3
    assert len(snippet.split("\n")) <= 5
