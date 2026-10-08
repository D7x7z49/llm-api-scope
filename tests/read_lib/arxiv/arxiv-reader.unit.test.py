# tests/read_lib/arxiv/arxiv-reader.unit.test.py
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from apiscope.cache import CacheMetadata, ContentKind
from apiscope.read_lib.arxiv.reader import ArxivReader
from apiscope.view_lib.arxiv.viewer import ArxivViewer

_CHILD = """<section id="S1.SS1" class="ltx_subsection">
<h3 class="ltx_title ltx_title_subsection">Child</h3>
<p>Child text.</p>
</section>"""


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


def test_arxiv_reader_returns_the_original_html_section(
    tmp_path: Path,
    document: Callable[[str], str],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "paper.html").write_text(document("arxiv/reader.html"), encoding="utf-8")
    metadata = _metadata(kind="file", name="paper.html")
    tree = ArxivViewer().build(content, metadata)
    target = tree.resolve("S1.SS1")

    result = ArxivReader().read(content, metadata, target)

    assert result.target == "S1.SS1"
    assert result.kind == "text"
    assert result.media_type == "text/html"
    assert result.content == _CHILD


def test_arxiv_reader_returns_tex_source_without_rewriting_it(
    tmp_path: Path,
    document: Callable[[str], str],
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    tex = document("arxiv/source.tex")
    (content / "paper.tex").write_text(tex, encoding="utf-8")
    metadata = _metadata(kind="file", name="paper.tex")
    target = ArxivViewer().build(content, metadata).resolve("paper.tex")

    result = ArxivReader().read(content, metadata, target)

    assert result.content == tex
    assert result.media_type == "text/x-tex"
