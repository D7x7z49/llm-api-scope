# tests/read_lib/schema.unit.test.py
from apiscope.read_lib.schema import ReadResult


def test_read_result_omits_binary_body_with_the_library_template() -> None:
    result = ReadResult(target="blob.bin", kind="binary", size=7)

    assert result.render_body() == "(binary content omitted; 7 bytes)"
