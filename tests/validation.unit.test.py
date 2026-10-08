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


class _Bounds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gt: int = Field(default=1, gt=0)
    le: int = Field(default=1, le=5)
    lt: int = Field(default=1, lt=10)


class _Text(BaseModel):
    text: str


class _Items(BaseModel):
    items: list[int]


def _failure(model: type[BaseModel], **values: Any) -> ValidationError:
    with pytest.raises(ValidationError) as raised:
        model(**values)
    return raised.value


def _error(**values: Any) -> ValidationError:
    return _failure(_Sample, **values)


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


def test_describe_reports_an_upper_length_rule() -> None:
    actual = describe(_error(name="abcdefghi", mode="file", count=1, code="ok"))

    assert actual == "[name] must be at most 8 characters, but 9 characters were given"


def test_describe_reports_an_integer_rule() -> None:
    actual = describe(_failure(_Bounds, gt="x"))

    assert actual == "[gt] must be an integer, but [x] was given"


def test_describe_reports_a_strict_lower_bound() -> None:
    actual = describe(_failure(_Bounds, gt=0))

    assert actual == "[gt] must be greater than 0, but [0] was given"


def test_describe_reports_a_non_strict_upper_bound() -> None:
    actual = describe(_failure(_Bounds, le=6))

    assert actual == "[le] must be at most 5, but [6] was given"


def test_describe_reports_a_strict_upper_bound() -> None:
    actual = describe(_failure(_Bounds, lt=10))

    assert actual == "[lt] must be less than 10, but [10] was given"


def test_describe_reports_a_text_type_rule() -> None:
    actual = describe(_failure(_Text, text=5))

    assert actual == "[text] must be text, but [5] was given"


def test_describe_falls_back_to_the_error_message() -> None:
    actual = describe(_failure(_Items, items=1))

    assert actual == "[items] input should be a valid list"
