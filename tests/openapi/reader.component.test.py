# tests/openapi/reader.component.test.py
#
# Component test for OpenapiReader using real OpenAPI fixtures.

from apiscope.openapi.reader import HttpMethod


def test_paths_from_spec(spec_reader, request):
    paths = spec_reader.paths
    if "[json]" in request.node.name:
        assert len(paths) == 13
        assert "/pet" in paths
    elif "[yaml]" in request.node.name:
        assert len(paths) == 2
        assert "/board" in paths


def test_get_operation_from_spec(spec_reader, request):
    if "[json]" in request.node.name:
        op = spec_reader.get_operation("/pet/{petId}", HttpMethod.GET)
        assert op["operationId"] == "getPetById"
        assert op["summary"] == "Find pet by ID."
    elif "[yaml]" in request.node.name:
        op = spec_reader.get_operation("/board", HttpMethod.GET)
        assert op["summary"] == "Get the whole board"


def test_resolve_ref_inlines_schema(spec_reader, request):
    if "[json]" in request.node.name:
        op = spec_reader.get_operation("/pet/{petId}", HttpMethod.GET)
        resolved = spec_reader.resolve_ref(op)
        schema = resolved["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" not in schema
    elif "[yaml]" in request.node.name:
        op = spec_reader.get_operation("/board/{row}/{column}", HttpMethod.PUT)
        resolved = spec_reader.resolve_ref(op)
        assert "$ref" not in str(resolved)
