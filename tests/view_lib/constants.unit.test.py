# tests/view_lib/constants.unit.test.py
from apiscope.view_lib.constants import (
    MESSAGE_TEMPLATES,
    OUTPUT_TEMPLATES,
    TREE_INVARIANT_MESSAGES,
    NodeLabel,
    ProjectionReason,
    TreeInvariant,
)


def test_every_projection_reason_has_a_message_template() -> None:
    assert {reason.value for reason in ProjectionReason} == set(MESSAGE_TEMPLATES)


def test_every_node_label_has_a_template() -> None:
    assert {label.value for label in NodeLabel} == set(OUTPUT_TEMPLATES)


def test_every_tree_invariant_has_a_message() -> None:
    assert {invariant.value for invariant in TreeInvariant} == set(TREE_INVARIANT_MESSAGES)
