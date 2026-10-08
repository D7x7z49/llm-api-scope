# tests/view_lib/arxiv/arxiv-viewer.unit.test.py
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apiscope.cache import CacheMetadata, ContentKind
from apiscope.view_lib.arxiv.viewer import ArxivViewer
from apiscope.view_lib.constants import ProjectionReason
from apiscope.view_lib.errors import ProjectionError

_HTML = """<!doctype html>
<html><body><article class="ltx_document">
<section id="S1" class="ltx_section">
<h2 class="ltx_title ltx_title_section"><span>1 </span>Introduction</h2>
<p>Parent text.</p>
<section id="S1.SS1" class="ltx_subsection">
<h3 class="ltx_title ltx_title_subsection"><span>1.1 </span>Child</h3>
<p>Child text.</p>
</section>
</section>
<section id="S2" class="ltx_section">
<h2 class="ltx_title ltx_title_section">Conclusion</h2>
<p>Final text.</p>
</section>
</article></body></html>
"""


def _metadata(*, kind: ContentKind, name: str | None) -> CacheMetadata:
    return CacheMetadata(
        format_version="1",
        doc_type="arxiv",
        source="1706.03762",
        source_digest="source-digest",
        fetched_at=datetime(2026, 10, 8, tzinfo=timezone.utc),
        content_kind=kind,
        content_name=name,
        content_digest="content-digest",
    )


def test_arxiv_viewer_builds_nested_section_routes(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "paper.html").write_text(_HTML, encoding="utf-8")

    tree = ArxivViewer().build(content, _metadata(kind="file", name="paper.html"))

    assert [(node.key, node.path) for node in tree.indexed()] == [
        ("1 Introduction", "S1"),
        ("1.1 Child", "S1.SS1"),
        ("Conclusion", "S2"),
    ]
    assert tree.resolve("S1.SS1").is_leaf
    assert not tree.resolve("S1").is_leaf


def test_arxiv_viewer_disambiguates_duplicate_titles_and_routes(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    html = (
        '<html><section id="S1" class="ltx_section"><h2 class="ltx_title">Same</h2></section>'
        '<section id="S1" class="ltx_section"><h2 class="ltx_title">Same</h2></section></html>'
    )
    (content / "paper.html").write_text(html, encoding="utf-8")

    tree = ArxivViewer().build(content, _metadata(kind="file", name="paper.html"))

    assert [(node.key, node.path) for node in tree.indexed()] == [("Same", "S1"), ("Same (S1-1)", "S1-1")]


def test_arxiv_viewer_uses_the_filesystem_tree_for_tex_source(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "paper.tex").write_text("\\documentclass{article}\n", encoding="utf-8")

    tree = ArxivViewer().build(content, _metadata(kind="file", name="paper.tex"))

    assert [(node.key, node.path) for node in tree.indexed()] == [("paper.tex", "paper.tex")]


def test_arxiv_viewer_rejects_html_without_sections(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "paper.html").write_text("<html><body>no sections</body></html>", encoding="utf-8")

    with pytest.raises(ProjectionError) as raised:
        ArxivViewer().build(content, _metadata(kind="file", name="paper.html"))

    assert raised.value.reason_code == ProjectionReason.CONTENT_INVALID
