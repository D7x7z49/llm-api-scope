# tests/rfc/parse_txt.unit.test.py

import pytest

from apiscope.rfc.parse_txt import extract_page, page_count, split_pages

TXT_FLAT = "one line\nno markers\n"

TXT_PAGED = """\
header before page 1.

                                   [Page 1]
\f
page 2 content line 1

                                   [Page 2]
\f
page 3 content here.

                                   [Page 3]
\f"""


@pytest.mark.parametrize(
    ("content", "expected"),
    [(TXT_FLAT, 1), (TXT_PAGED, 3)],
    ids=["flat", "paged"],
)
def test_page_count(content, expected):
    assert page_count(content) == expected


def test_split_pages_no_markers():
    pages = split_pages(TXT_FLAT)
    assert len(pages) == 1
    assert pages[0][0] == 1


def test_split_pages_with_markers():
    pages = split_pages(TXT_PAGED)
    page_nums = [p for p, _, _ in pages]
    assert page_nums[:3] == [1, 2, 3]


def test_extract_page_happy_path():
    content = extract_page(TXT_PAGED, 3)
    assert "page 3 content" in content


def test_extract_page_not_found():
    with pytest.raises(ValueError, match="page 99 not found"):
        extract_page(TXT_PAGED, 99)
