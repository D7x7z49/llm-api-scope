# tests/sync/_lib/arxiv/arxiv-fetcher.unit.test.py
from __future__ import annotations

import gzip
import tarfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import httpx2
import pytest

from apiscope.source import ArxivSource, parse_source
from apiscope.sync._lib.arxiv.fetcher import ArxivFetcher
from apiscope.sync._lib.errors import SourceFetchError


def _source() -> ArxivSource:
    return parse_source("arxiv", "1706.03762v7", base_dir=Path.cwd())  # type: ignore[return-value]


def _archive(files: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with tarfile.open(fileobj=output, mode="w") as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, BytesIO(data))
    return gzip.compress(output.getvalue())


def test_arxiv_fetcher_prefers_html(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[str] = []
    html = b'<html><article class="ltx_document"><h1>Paper</h1></article></html>'

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        return httpx2.Response(200, content=html)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    result = ArxivFetcher().fetch(_source(), destination=destination)

    assert requests == ["https://arxiv.org/html/1706.03762v7"]
    assert result.content_kind == "file"
    assert result.content_name == "paper.html"
    assert (destination / "content" / "paper.html").read_bytes() == html


def test_arxiv_fetcher_falls_back_to_a_single_tex_file(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[str] = []
    tex = b"\\documentclass{article}\\begin{document}paper\\end{document}"

    def handler(request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        requests.append(url)
        if "/html/" in url:
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=gzip.compress(tex))

    install_mock_client(handler)
    destination = tmp_path / "staging"

    result = ArxivFetcher().fetch(_source(), destination=destination)

    assert requests == [
        "https://arxiv.org/html/1706.03762v7",
        "https://arxiv.org/e-print/1706.03762v7",
    ]
    assert result.content_kind == "file"
    assert result.content_name == "paper.tex"
    assert (destination / "content" / "paper.tex").read_bytes() == tex


def test_arxiv_fetcher_falls_back_when_html_is_not_a_paper(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    requests: list[str] = []
    tex = b"\\documentclass{article}\\begin{document}paper\\end{document}"

    def handler(request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        requests.append(url)
        if "/html/" in url:
            return httpx2.Response(200, content=b"<html>conversion unavailable</html>", request=request)
        return httpx2.Response(200, content=gzip.compress(tex), request=request)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    result = ArxivFetcher().fetch(_source(), destination=destination)

    assert requests == [
        "https://arxiv.org/html/1706.03762v7",
        "https://arxiv.org/e-print/1706.03762v7",
    ]
    assert result.content_name == "paper.tex"
    assert (destination / "content" / "paper.tex").read_bytes() == tex


def test_arxiv_fetcher_unpacks_a_safe_tex_archive(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    tex = b"\\section{Introduction}"
    archive = _archive({"paper/main.tex": tex, "paper/figure.png": b"figure"})

    def handler(request: httpx2.Request) -> httpx2.Response:
        if "/html/" in str(request.url):
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=archive)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    result = ArxivFetcher().fetch(_source(), destination=destination)

    assert result.content_kind == "directory"
    assert result.content_name is None
    assert (destination / "content" / "paper" / "main.tex").read_bytes() == tex
    assert (destination / "content" / "paper" / "figure.png").read_bytes() == b"figure"


def test_arxiv_fetcher_rejects_pdf_only_papers_without_storing_the_pdf(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    pdf = b"%PDF-1.7 pdf-only paper"

    def handler(request: httpx2.Request) -> httpx2.Response:
        if "/html/" in str(request.url):
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=pdf)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    with pytest.raises(SourceFetchError) as raised:
        ArxivFetcher().fetch(_source(), destination=destination)

    assert raised.value.reason_code == "fetch.arxiv_no_structured_source"
    assert list((destination / "content").iterdir()) == []


@pytest.mark.parametrize(
    "payload",
    [
        b"%!PS-Adobe-3.0 PostScript",
        gzip.compress(b"%!PS-Adobe-3.0 PostScript"),
        b"\xf7\x02dvi data",
        b"<html>temporary error</html>",
    ],
)
def test_arxiv_fetcher_rejects_non_tex_eprint_payloads(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
    payload: bytes,
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if "/html/" in str(request.url):
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=payload, request=request)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    with pytest.raises(SourceFetchError) as raised:
        ArxivFetcher().fetch(_source(), destination=destination)

    assert raised.value.reason_code == "fetch.arxiv_no_structured_source"
    assert list((destination / "content").iterdir()) == []


def test_arxiv_fetcher_rejects_archive_path_traversal(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    archive = _archive({"../outside.tex": b"unsafe"})

    def handler(request: httpx2.Request) -> httpx2.Response:
        if "/html/" in str(request.url):
            return httpx2.Response(404, request=request)
        return httpx2.Response(200, content=archive)

    install_mock_client(handler)
    destination = tmp_path / "staging"

    with pytest.raises(SourceFetchError) as raised:
        ArxivFetcher().fetch(_source(), destination=destination)

    assert raised.value.reason_code == "fetch.arxiv_source_invalid"
    assert not (tmp_path / "outside.tex").exists()


def test_arxiv_fetcher_reports_non_404_html_errors(
    tmp_path: Path,
    install_mock_client: Callable[[Callable[[httpx2.Request], httpx2.Response]], None],
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(503, request=request)

    install_mock_client(handler)

    with pytest.raises(SourceFetchError) as raised:
        ArxivFetcher().fetch(_source(), destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.transport_failed"
    assert isinstance(raised.value.__cause__, httpx2.HTTPStatusError)
