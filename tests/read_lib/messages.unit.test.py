# tests/read_lib/messages.unit.test.py
import pytest

from apiscope.read.constants import MESSAGE_TEMPLATES as READ_MESSAGE_TEMPLATES
from apiscope.read_lib.constants import (
    INVARIANT_MESSAGES,
    MESSAGE_TEMPLATES,
    OUTPUT_TEMPLATES,
    ReadInvariant,
    ReadOutput,
    ReadReason,
)


def test_every_read_reason_has_a_message_template() -> None:
    assert {reason.value for reason in ReadReason} == set(MESSAGE_TEMPLATES)


def test_every_read_result_output_has_a_template() -> None:
    assert {output.value for output in ReadOutput} == set(OUTPUT_TEMPLATES)


def test_every_read_invariant_has_a_message() -> None:
    assert {invariant.value for invariant in ReadInvariant} == set(INVARIANT_MESSAGES)


@pytest.mark.parametrize(
    "templates",
    [READ_MESSAGE_TEMPLATES, MESSAGE_TEMPLATES],
    ids=["read", "read_lib"],
)
def test_read_message_templates_do_not_contain_colons(templates: dict[str, str]) -> None:
    invalid_keys = [key for key, value in templates.items() if ":" in value]

    assert invalid_keys == []
