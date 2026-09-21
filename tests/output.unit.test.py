# tests/output.unit.test.py
import io
import json

import pytest

from apiscope.add.constants import MESSAGE_TEMPLATES as ADD_MESSAGE_TEMPLATES
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.list.constants import MESSAGE_TEMPLATES as LIST_MESSAGE_TEMPLATES
from apiscope.output import OutputError, OutputFormat, Report, emit_report, render_report
from apiscope.remove.constants import MESSAGE_TEMPLATES as REMOVE_MESSAGE_TEMPLATES
from apiscope.sync.constants import MESSAGE_TEMPLATES as SYNC_MESSAGE_TEMPLATES


@pytest.mark.parametrize(
    "templates",
    [
        ROOT_MESSAGE_TEMPLATES,
        ADD_MESSAGE_TEMPLATES,
        LIST_MESSAGE_TEMPLATES,
        REMOVE_MESSAGE_TEMPLATES,
        SYNC_MESSAGE_TEMPLATES,
    ],
    ids=["root", "add", "list", "remove", "sync"],
)
def test_error_message_templates_do_not_contain_colons(templates: dict[str, str]) -> None:
    invalid_keys = [key for key, value in templates.items() if ".error." in key and ":" in value]

    assert invalid_keys == []


def test_render_text_for_write_success_orders_scope_before_action() -> None:
    report = Report(
        status="ok",
        scope="project",
        action="add",
        meta={"type": "openapi", "name": "petstore"},
    )

    actual = render_report(report)

    assert actual == "[ok] [scope=project] [action=add] [name=petstore] [type=openapi]"


def test_render_text_for_error_uses_the_message_template_key_as_code() -> None:
    report = Report(
        status="error",
        scope="project",
        action="add",
        code="add.error.duplicate_name",
        meta={"name": "petstore"},
    )
    templates = {"add.error.duplicate_name": "source {name} already exists"}

    actual = render_report(report, message_templates=templates)

    assert actual == (
        "[error] [scope=project] [action=add] [code=add.error.duplicate_name] "
        "[name=petstore]: source petstore already exists"
    )


def test_render_json_for_write_success_omits_message_and_read_fields() -> None:
    report = Report(
        status="ok",
        scope="home",
        action="remove",
        meta={"name": "petstore"},
    )

    actual = json.loads(render_report(report, output_format=OutputFormat.JSON))

    assert actual == {
        "status": "ok",
        "scope": "home",
        "action": "remove",
        "meta": {"name": "petstore"},
    }


def test_render_json_for_read_success_contains_data_and_extra() -> None:
    report = Report(
        status="ok",
        scope="project",
        action="list",
        meta={"filter": "openapi"},
        data=[{"name": "petstore", "type": "openapi"}],
        extra={"total": 1, "count": 1},
    )

    actual = json.loads(render_report(report, output_format="json"))

    assert actual == {
        "status": "ok",
        "scope": "project",
        "action": "list",
        "meta": {"filter": "openapi"},
        "data": [{"name": "petstore", "type": "openapi"}],
        "extra": {"count": 1, "total": 1},
    }


def test_render_json_for_error_includes_code_and_message() -> None:
    report = Report(
        status="error",
        scope="home",
        action="remove",
        code="remove.error.name_not_found",
        meta={"name": "petstore"},
        message="source was not found",
    )

    actual = json.loads(render_report(report, output_format="json"))

    assert actual == {
        "status": "error",
        "scope": "home",
        "action": "remove",
        "code": "remove.error.name_not_found",
        "meta": {"name": "petstore"},
        "message": "source was not found",
    }


def test_render_text_for_read_success_has_head_body_and_foot() -> None:
    report = Report(
        status="ok",
        scope="project",
        action="list",
        data=[{"name": "petstore"}],
        extra={"count": 1},
    )

    actual = render_report(report, body="petstore", foot="count 1")

    assert actual == "[ok] [scope=project] [action=list]\n\n---\n\npetstore\n\n---\n\ncount 1"


def test_emit_report_writes_one_line_to_the_given_stream() -> None:
    report = Report(status="ok", scope="home", action="add")
    stream = io.StringIO()

    emit_report(report, stream=stream)

    assert stream.getvalue() == "[ok] [scope=home] [action=add]\n"


@pytest.mark.parametrize(
    ("status", "scope", "kwargs", "message"),
    [
        ("done", "project", {}, "report status"),
        ("ok", "local", {}, "report scope"),
        ("ok", "project", {"code": "add.error.invalid"}, "successful reports"),
        ("ok", "project", {"message": "done"}, "successful reports"),
        ("error", "project", {}, "error reports require"),
    ],
)
def test_report_rejects_invalid_envelope_values(
    status: str,
    scope: str,
    kwargs: dict[str, str],
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        Report(status=status, scope=scope, action="add", **kwargs)  # type: ignore[arg-type]


def test_report_requires_read_data_and_extra_together() -> None:
    with pytest.raises(ValueError, match="data and extra"):
        Report(status="ok", scope="project", action="list", data=[])


def test_render_error_requires_a_message_or_a_template() -> None:
    report = Report(status="error", scope="project", action="add", code="add.error.invalid")

    with pytest.raises(OutputError, match="missing its message"):
        render_report(report)


def test_render_error_rejects_a_missing_template_key() -> None:
    report = Report(status="error", scope="project", action="add", code="add.error.invalid")

    with pytest.raises(OutputError, match="no message template"):
        render_report(report, message_templates={})


def test_text_tags_encode_values_that_conflict_with_the_report_syntax() -> None:
    report = Report(
        status="ok",
        scope="project",
        action="add",
        meta={"name": "pet store:blue"},
    )

    actual = render_report(report)

    assert actual == "[ok] [scope=project] [action=add] [name=pet%20store%3Ablue]"
