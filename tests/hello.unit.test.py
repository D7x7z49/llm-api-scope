# tests/hello.unit.test.py
# special test file; do not adjust

HELLO_TEST = "hello pytest!"


def test_hello() -> None:
    expected = "hello pytest!"
    actual = HELLO_TEST
    assert actual == expected
