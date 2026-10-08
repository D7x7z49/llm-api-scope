# tests/validation.unit.test.py

from typing import Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apiscope.validation import describe


class _Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=8)
    mode: Literal["file", "view"]
    count: int = Field(ge=1)
    code: str = Field(pattern=r"^[a-z]+$")


def _error(**values: Any) -> ValidationError:
    with pytest.raises(ValidationError) as raised:
        _Sample(**values)
    return raised.value


def test_describe_reports_a_length_rule_and_the_observed_size() -> None:
    actual = describe(_error(name="ab", mode="file", count=1, code="ok"))

    assert actual == "[name] must be at least 3 characters, but 2 characters were given"


def test_describe_reports_a_literal_choice_and_the_observed_value() -> None:
    actual = describe(_error(name="abc", mode="read", count=1, code="ok"))

    assert actual == "[mode] must be one of 'file' or 'view', but [read] was given"


def test_describe_reports_a_lower_bound_and_the_observed_value() -> None:
    actual = describe(_error(name="abc", mode="file", count=0, code="ok"))

    assert actual == "[count] must be at least 1, but [0] was given"


def test_describe_reports_a_pattern_and_the_observed_value() -> None:
    actual = describe(_error(name="abc", mode="file", count=1, code="UP"))

    assert actual == "[code] must match the pattern ^[a-z]+$, but [UP] was given"


def test_describe_reports_a_required_field_and_an_unexpected_field() -> None:
    actual = describe(_error(name="abc", mode="file", extra="x"))

    assert "[code] is required" in actual
    assert "[extra] is not an accepted option" in actual


def test_describe_maps_a_field_name_to_its_option_label() -> None:
    actual = describe(_error(name="ab", mode="file", count=1, code="ok"), {"name": "--name"})

    assert actual.startswith("[--name] must be at least 3 characters")


def test_describe_truncates_a_long_value() -> None:
    actual = describe(_error(name="abc", mode="file", count=1, code="A" * 100))

    assert "..." in actual
    assert actual.endswith("] was given")
