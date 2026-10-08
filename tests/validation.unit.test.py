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


def _error(model: type[BaseModel], values: dict[str, Any]) -> ValidationError:
    with pytest.raises(ValidationError) as raised:
        model(**values)
    return raised.value


# one behavior, describe renders a finding; the error type is the enumerable input
@pytest.mark.parametrize(
    ("model", "values", "expected"),
    [
        pytest.param(
            _Sample,
            {"name": "ab", "mode": "file", "count": 1, "code": "ok"},
            "[name] must be at least 3 characters, but 2 characters were given",
            id="string-too-short",
        ),
        pytest.param(
            _Sample,
            {"name": "abcdefghi", "mode": "file", "count": 1, "code": "ok"},
            "[name] must be at most 8 characters, but 9 characters were given",
            id="string-too-long",
        ),
        pytest.param(
            _Sample,
            {"name": "abc", "mode": "read", "count": 1, "code": "ok"},
            "[mode] must be one of 'file' or 'view', but [read] was given",
            id="literal-choice",
        ),
        pytest.param(
            _Sample,
            {"name": "abc", "mode": "file", "count": 0, "code": "ok"},
            "[count] must be at least 1, but [0] was given",
            id="lower-bound",
        ),
        pytest.param(
            _Sample,
            {"name": "abc", "mode": "file", "count": 1, "code": "UP"},
            "[code] must match the pattern ^[a-z]+$, but [UP] was given",
            id="pattern",
        ),
        pytest.param(
            _Bounds,
            {"gt": "x"},
            "[gt] must be an integer, but [x] was given",
            id="integer-parse",
        ),
        pytest.param(
            _Bounds,
            {"gt": 0},
            "[gt] must be greater than 0, but [0] was given",
            id="strict-lower-bound",
        ),
        pytest.param(
            _Bounds,
            {"le": 6},
            "[le] must be at most 5, but [6] was given",
            id="upper-bound",
        ),
        pytest.param(
            _Bounds,
            {"lt": 10},
            "[lt] must be less than 10, but [10] was given",
            id="strict-upper-bound",
        ),
        pytest.param(
            _Text,
            {"text": 5},
            "[text] must be text, but [5] was given",
            id="text-type",
        ),
        pytest.param(
            _Items,
            {"items": 1},
            "[items] input should be a valid list",
            id="message-fallback",
        ),
    ],
)
def test_describe_renders_a_finding(
    model: type[BaseModel],
    values: dict[str, Any],
    expected: str,
) -> None:
    assert describe(_error(model, values)) == expected


def test_describe_reports_a_required_field_and_an_unexpected_field() -> None:
    actual = describe(_error(_Sample, {"name": "abc", "mode": "file", "extra": "x"}))

    assert "[code] is required" in actual
    assert "[extra] is not an accepted option" in actual


def test_describe_maps_a_field_name_to_its_option_label() -> None:
    actual = describe(
        _error(_Sample, {"name": "ab", "mode": "file", "count": 1, "code": "ok"}),
        {"name": "--name"},
    )

    assert actual.startswith("[--name] must be at least 3 characters")


def test_describe_truncates_a_long_value() -> None:
    actual = describe(_error(_Sample, {"name": "abc", "mode": "file", "count": 1, "code": "A" * 100}))

    assert "..." in actual
    assert actual.endswith("] was given")
