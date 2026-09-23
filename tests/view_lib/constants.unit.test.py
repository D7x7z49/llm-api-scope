# tests/view_lib/constants.unit.test.py
from apiscope.view_lib.constants import MESSAGE_TEMPLATES, ProjectionReason


def test_every_projection_reason_has_a_message_template() -> None:
    assert {reason.value for reason in ProjectionReason} == set(MESSAGE_TEMPLATES)
