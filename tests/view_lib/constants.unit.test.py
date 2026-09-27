# tests/view_lib/constants.unit.test.py
from apiscope.view_lib.constants import (
    MESSAGE_TEMPLATES,
    OUTPUT_TEMPLATES,
    TREE_INVARIANT_MESSAGES,
    NodeLabel,
    ProjectionReason,
    TreeInvariant,
    ViewOutput,
)


def test_every_projection_reason_has_a_message_template() -> None:
    assert {reason.value for reason in ProjectionReason} == set(MESSAGE_TEMPLATES)


def test_every_node_label_and_output_has_a_template() -> None:
    labels = {label.value for label in NodeLabel} | {output.value for output in ViewOutput}
    assert labels == set(OUTPUT_TEMPLATES)


def test_every_tree_invariant_has_a_message() -> None:
    assert {invariant.value for invariant in TreeInvariant} == set(TREE_INVARIANT_MESSAGES)
