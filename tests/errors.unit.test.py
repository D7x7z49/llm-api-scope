# tests/errors.unit.test.py
import pytest

from apiscope.errors import MessageError


def test_message_error_keeps_code_and_values_and_formats_default_message() -> None:
    error = MessageError("root.error.config.invalid", {"path": "/tmp/config.json"})

    assert error.code == "root.error.config.invalid"
    assert error.values == {"path": "/tmp/config.json"}
    assert str(error) == "configuration at /tmp/config.json is invalid. fix or remove it before retrying"


def test_message_error_returns_code_when_the_catalog_key_is_unknown() -> None:
    error = MessageError("root.error.unknown")

    assert str(error) == "root.error.unknown"


@pytest.mark.parametrize(
    "code",
    ["", "Root.error.invalid", "root error invalid", "root:error:invalid"],
)
def test_message_error_rejects_invalid_codes(code: str) -> None:
    with pytest.raises(ValueError, match="dotted lower-case key"):
        MessageError(code)


def test_message_error_rejects_non_mapping_values() -> None:
    with pytest.raises(TypeError, match="provided as a mapping"):
        MessageError("root.error.invalid", [])  # type: ignore[arg-type]
