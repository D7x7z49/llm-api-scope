# tests/openapi/reader.unit.test.py
#
# unit tests for OpenapiReader — in-memory hand-crafted payloads.

import pytest

from apiscope.openapi.reader import HttpMethod

# ==============================================================================
# filter_paths
# ==============================================================================


@pytest.mark.parametrize(
    "methods,expected_count",
    [
        ((HttpMethod.GET,), 2),
        ((HttpMethod.GET, HttpMethod.POST), 2),
        ((HttpMethod.PATCH,), 0),
    ],
    ids=["get-only", "get-post", "no-match"],
)
def test_filter_paths(inline_reader, methods, expected_count):
    result = inline_reader.filter_paths(*methods)
    assert len(result) == expected_count


# ==============================================================================
# resolve_ref
# ==============================================================================


def test_resolve_ref_replaces_local_ref(ref_reader):
    op = ref_reader.get_operation("/pets", HttpMethod.GET)
    resolved = ref_reader.resolve_ref(op)
    schema = resolved["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" not in schema
    assert schema["type"] == "object"


def test_resolve_ref_skips_external_url(ref_reader):
    data = {"schema": {"$ref": "https://external.com/spec.yaml#/Foo"}}
    resolved = ref_reader.resolve_ref(data)
    assert resolved == data


def test_resolve_ref_skips_unknown_local_path(ref_reader):
    data = {"schema": {"$ref": "#/components/schemas/Unknown"}}
    resolved = ref_reader.resolve_ref(data)
    assert resolved == data
