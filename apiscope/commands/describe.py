# apiscope/commands/describe.py
"""
Generate structured JSON documentation for a specific API endpoint.
Uses LogLight-style output for consistent, concise logging.
"""
import json
from typing import Any, Tuple, Dict, Optional

import click

from ..core.output import OutputBuilder
from ..core.config import GLOBAL_CONFIG
from ..core.parser import get_spec, ParserError


def _parse_path_method(path_method: str) -> Tuple[str, str]:
    """
    Parse path:method string into separate components.

    Args:
        path_method: String in format "path:method"

    Returns:
        Tuple of (path, method_lowercase)

    Raises:
        ValueError: If format is invalid
    """
    if ":" not in path_method:
        raise ValueError(f"Invalid format: '{path_method}'. Use 'path:method'.")

    path, method = path_method.rsplit(":", 1)
    if not path or not method:
        raise ValueError(f"Invalid format: '{path_method}'. Both path and method required.")

    # Clean up path and validate method
    path = path.strip()
    method = method.strip().lower()

    # Validate HTTP method
    valid_methods = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}
    if method not in valid_methods:
        raise ValueError(f"Invalid HTTP method: '{method}'. Must be one of: {', '.join(sorted(valid_methods))}")

    return path, method


def _extract_schema_basics(spec: Any, schema: Any) -> Dict[str, Any]:
    """
    Extract basic schema information for LLM understanding.
    Returns essential fields without deep recursion.

    Args:
        spec: OpenAPI object for reference resolution
        schema: SchemaPath object or dict

    Returns:
        Dictionary with basic schema information
    """
    if not schema:
        return {"type": "unknown"}

    try:
        result = {}

        # Handle references first - resolve to actual content
        if "$ref" in schema:
            ref = str(schema["$ref"])
            try:
                # Parse reference path: remove #/ prefix and split by /
                if ref.startswith("#/"):
                    path_parts = ref[2:].split("/")  # Remove #/ and split
                else:
                    path_parts = ref.split("/")

                # Navigate to the referenced schema using SchemaPath / operator
                resolved = spec.spec
                for part in path_parts:
                    resolved = resolved / part

                # Recursively extract info from resolved schema
                result = _extract_schema_basics(spec, resolved)
                # Keep original reference info for context
                result["$ref"] = ref
                if "#/components/schemas/" in ref:
                    result["ref_type"] = "schema"
                    result["schema_name"] = ref.split("/")[-1]
                elif "#/components/parameters/" in ref:
                    result["ref_type"] = "parameter"
                elif "#/components/responses/" in ref:
                    result["ref_type"] = "response"
            except Exception:
                # Fallback to reference info only if resolution fails
                result["$ref"] = ref
                if "#/components/schemas/" in ref:
                    result["ref_type"] = "schema"
                    result["schema_name"] = ref.split("/")[-1]
                elif "#/components/parameters/" in ref:
                    result["ref_type"] = "parameter"
                elif "#/components/responses/" in ref:
                    result["ref_type"] = "response"

        # Handle arrays
        elif "items" in schema:
            result["type"] = "array"
            result["items"] = _extract_schema_basics(spec, schema["items"])

        # Handle object properties (limited depth)
        elif "properties" in schema:
            result["type"] = "object"
            properties = schema["properties"]

            # Extract a few key properties for context
            sample_props = {}
            for i, (prop_name, prop_schema) in enumerate(properties.items()):
                if i >= 3:  # Limit to 3 properties for brevity
                    sample_props["_more"] = f"{len(properties) - 3} more properties"
                    break
                prop_info = _extract_schema_basics(spec, prop_schema)
                sample_props[str(prop_name)] = prop_info

            result["properties"] = sample_props

            if "required" in schema:
                result["required"] = [str(r) for r in schema["required"]]

        # Default: extract basic type information
        if "type" in schema:
            result["type"] = str(schema["type"])
            if "format" in schema:
                result["format"] = str(schema["format"])

        # Handle required field
        if "required" in schema:
            result["required"] = bool(schema["required"])

        # Handle enum values
        if "enum" in schema:
            result["enum"] = [str(v) for v in schema["enum"][:5]]  # Limit enum values

        return result

    except Exception:
        return {"type": "object"}


def _extract_operation_info(spec: Any, path: str, method: str) -> dict:
    """
    Extract operation information with meaningful schema details.

    Args:
        spec: OpenAPI object
        path: API path
        method: HTTP method (lowercase)

    Returns:
        Dictionary with operation information

    Raises:
        KeyError: If path or method not found
    """
    # Try SchemaPath navigation first
    try:
        operation = spec.spec / "paths" / path / method
    except (KeyError, TypeError):
        # Fall back to dictionary navigation
        paths = spec.spec.get("paths", {})
        if path not in paths:
            available_paths = list(paths.keys())
            display_paths = available_paths[:5]
            extra = f" (+{len(available_paths)-5} more)" if len(available_paths) > 5 else ""
            raise KeyError(f"Path '{path}' not found. Available: {', '.join(display_paths)}{extra}")

        path_obj = paths[path]
        if method not in path_obj:
            available_methods = list(path_obj.keys())
            raise KeyError(f"Method '{method}' not found for path '{path}'. Available: {', '.join(available_methods)}")

        operation = path_obj[method]

    # Build structured result
    result = {
        "path": path,
        "method": method.upper(),
    }

    # Extract scalar fields
    for field in ["summary", "description", "operationId"]:
        if field in operation:
            result[field] = str(operation[field])

    # Extract parameters with meaningful schema info
    if "parameters" in operation:
        result["parameters"] = []
        for param in operation["parameters"]:
            param_info = {}

            # Basic parameter fields
            for field in ["name", "in", "description"]:
                if field in param:
                    param_info[field] = str(param[field])

            # Required field
            if "required" in param:
                param_info["required"] = bool(param["required"])

            # Schema information
            if "schema" in param:
                param_info["schema"] = _extract_schema_basics(spec, param["schema"])

            result["parameters"].append(param_info)

    # Extract requestBody with meaningful content
    if "requestBody" in operation:
        request_body = operation["requestBody"]
        body_info = {}

        # Basic fields
        for field in ["description", "required"]:
            if field in request_body:
                if field == "required":
                    body_info[field] = bool(request_body[field])
                else:
                    body_info[field] = str(request_body[field])

        # Content with schema details
        if "content" in request_body:
            content_info = {}
            content = request_body["content"]

            for media_type in content:
                media_info = content[media_type]
                media_type_info = {}

                if "schema" in media_info:
                    media_type_info["schema"] = _extract_schema_basics(spec, media_info["schema"])

                content_info[media_type] = media_type_info

            body_info["content"] = content_info

        result["requestBody"] = body_info

    # Extract responses with meaningful content
    if "responses" in operation:
        result["responses"] = {}
        for status_code, response in operation["responses"].items():
            response_info = {}

            if "description" in response:
                response_info["description"] = str(response["description"])

            if "content" in response:
                content_info = {}
                content = response["content"]

                for media_type in content:
                    media_info = content[media_type]
                    media_type_info = {}

                    if "schema" in media_info:
                        media_type_info["schema"] = _extract_schema_basics(spec, media_info["schema"])

                    content_info[media_type] = media_type_info

                response_info["content"] = content_info

            result["responses"][str(status_code)] = response_info

    # Extract security requirements
    if "security" in operation:
        result["security"] = []
        for sec_item in operation["security"]:
            for scheme_name, scopes in sec_item.items():
                security_info = {
                    "scheme": str(scheme_name),
                    "scopes": [str(scope) for scope in scopes] if scopes else []
                }
                result["security"].append(security_info)

    return result


@click.command()
@click.argument("name", type=str)
@click.argument("path_method", type=str)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force refresh cache for remote specifications"
)
@click.option(
    "--pretty",
    is_flag=True,
    default=False,
    help="Pretty-print JSON output with indentation"
)
def describe_command(name: str, path_method: str, force: bool, pretty: bool):
    """
    Generate structured JSON documentation for a specific API endpoint.

    NAME: Name of the API specification from configuration
    PATH_METHOD: Endpoint identifier in format "path:method"
    """
    output = OutputBuilder()
    output.section("Describe")

    # Check if configuration is initialized
    if not GLOBAL_CONFIG.is_initialized:
        output.action("Checking configuration state")
        output.note("Configuration not initialized")
        output.note("Run 'apiscope init' first")
        output.complete("Describe")
        output.emit()
        return

    try:
        # Parse input parameters
        output.action("Parsing endpoint identifier")
        try:
            path, method = _parse_path_method(path_method)
            output.result(f"Parsed: path='{path}', method='{method.upper()}'")
        except ValueError as e:
            output.error(f"Invalid format: {e}")
            output.note("Use format: path:method (e.g., /pet:PUT)")
            output.complete("Describe")
            output.emit()
            raise click.ClickException("Describe failed")

        # Get the specification
        output.action(f"Loading specification: {name}")
        try:
            spec = get_spec(name, force)
            output.result("Specification loaded successfully")
        except ParserError as e:
            output.error(f"Failed to load specification: {e}")
            output.complete("Describe")
            output.emit()
            raise click.ClickException("Describe failed")

        # Extract operation information
        output.action(f"Locating endpoint: {path}:{method.upper()}")
        try:
            operation_info = _extract_operation_info(spec, path, method)
            output.result("Endpoint found")
        except KeyError as e:
            output.error(f"Endpoint not found: {e}")
            output.complete("Describe")
            output.emit()
            raise click.ClickException("Describe failed")

        # Generate JSON output
        output.action("Generating JSON documentation")

        # Convert to JSON with appropriate formatting
        indent = 2 if pretty else None
        json_output = json.dumps(operation_info, indent=indent, ensure_ascii=False)

        output.result("JSON documentation generated")
        output.complete("Describe")

        # Output process log first, then JSON
        output.emit()
        print()  # Add blank line for separation
        print(json_output)

    except Exception as e:
        # Catch any unexpected errors
        output.error(f"Unexpected error: {e}")
        output.complete("Describe")
        output.emit()
        raise click.ClickException("Describe failed")


if __name__ == "__main__":
    describe_command()
