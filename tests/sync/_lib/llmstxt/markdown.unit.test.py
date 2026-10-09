# tests/sync/_lib/llmstxt/markdown.unit.test.py
from apiscope.sync._lib.llmstxt.markdown import is_html, markdown_candidates


def test_markdown_candidates_prefers_the_replaced_extension() -> None:
    assert markdown_candidates("https://example.test/docs/page.html") == [
        "https://example.test/docs/page.md",
        "https://example.test/docs/page.html.md",
    ]


def test_markdown_candidates_uses_an_index_for_a_name_without_a_file() -> None:
    assert markdown_candidates("https://example.test/docs/guide") == [
        "https://example.test/docs/guide.md",
        "https://example.test/docs/guide/index.md",
        "https://example.test/docs/guide/index.html.md",
    ]


def test_markdown_candidates_keeps_a_markdown_target() -> None:
    assert markdown_candidates("https://example.test/docs/guide.md") == []
    assert markdown_candidates("https://example.test/docs/guide.markdown") == []


def test_markdown_candidates_handles_the_origin_root() -> None:
    assert markdown_candidates("https://example.test") == [
        "https://example.test/index.md",
        "https://example.test/index.html.md",
    ]


def test_markdown_candidates_keeps_the_query_and_drops_the_fragment() -> None:
    assert markdown_candidates("https://example.test/docs/guide?q=1#top") == [
        "https://example.test/docs/guide.md?q=1",
        "https://example.test/docs/guide/index.md?q=1",
        "https://example.test/docs/guide/index.html.md?q=1",
    ]


def test_is_html_detects_a_document_shell() -> None:
    assert is_html(b"<!doctype html><html></html>")
    assert is_html(b'  <html lang="en">')
    assert not is_html(b"# Guide\n")
