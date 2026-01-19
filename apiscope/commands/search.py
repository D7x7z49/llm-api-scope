# apiscope/commands/search.py
"""
Search for endpoints in an API specification.
Uses LogLight-style output for consistent, concise logging.
"""
import click
from typing import List, Dict, Any

from ..core.output import OutputBuilder
from ..core.config import GLOBAL_CONFIG
from ..core.parser import get_spec, ParserError


# Display limit - using 16 for binary-friendly boundary
DISPLAY_LIMIT = 16


def _search_endpoints(
    spec: Any,
    keywords: str,
    output: OutputBuilder
) -> List[Dict[str, str]]:
    """
    Search for endpoints matching keywords in the specification.

    Args:
        spec: OpenAPI object
        keywords: Search keywords (space-separated, all must match)
        output: OutputBuilder for logging

    Returns:
        List of matching endpoints, each as dict with 'path' and 'method'
    """
    matches = []
    keyword_list = [k.lower() for k in keywords.split() if k]

    if not keyword_list:
        output.note("No keywords provided, returning all endpoints")
        keyword_list = []

    output.action("Searching in specification")

    # Use SchemaPath navigation
    paths = spec.spec.get("paths", {})

    for path, path_obj in paths.items():
        for method, operation in path_obj.items():
            # Build searchable text from operation fields
            search_text = []

            # Use direct indexing to get actual values
            if "summary" in operation:
                search_text.append(str(operation["summary"]).lower())

            if "description" in operation:
                search_text.append(str(operation["description"]).lower())

            if "operationId" in operation:
                search_text.append(str(operation["operationId"]).lower())

            # Also include the path itself in search
            search_text.append(path.lower())

            # Check if all keywords match
            text_to_search = " ".join(search_text)
            all_keywords_match = all(
                keyword in text_to_search
                for keyword in keyword_list
            )

            if all_keywords_match:
                matches.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": str(operation["summary"]) if "summary" in operation else "",
                    "operation_id": str(operation["operationId"]) if "operationId" in operation else ""
                })

    return matches


def _get_search_quality(total_matches: int, display_count: int) -> str:
    """
    Assess search quality based on result count.

    Args:
        total_matches: Total number of matches found
        display_count: Number of matches being displayed

    Returns:
        Quality assessment string
    """
    if total_matches == 0:
        return "No results - try different keywords"
    elif total_matches == 1:
        return "Perfect match"
    elif total_matches <= 5:
        return "Good specificity"
    elif total_matches <= display_count:  # <= DISPLAY_LIMIT
        return "Moderate specificity"
    else:
        return "Broad search - consider narrowing"


@click.command()
@click.argument("name", type=str)
@click.argument("keywords", type=str)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force refresh cache for remote specifications"
)
def search_command(name: str, keywords: str, force: bool):
    """
    Search within an API specification for endpoints matching keywords.

    NAME: Name of the API specification from configuration
    KEYWORDS: Space-separated keywords to search for (all must match)
    """
    output = OutputBuilder()
    output.section("Search")

    # Check if configuration is initialized
    if not GLOBAL_CONFIG.is_initialized:
        output.action("Checking configuration state")
        output.note("Configuration not initialized")
        output.note("Run 'apiscope init' first")
        output.complete("Search")
        output.emit()
        return

    try:
        # 1. Get the specification
        output.action(f"Loading specification: {name}")
        try:
            spec = get_spec(name, force)
            output.result("Specification loaded successfully")
        except ParserError as e:
            output.error(f"Failed to load specification: {e}")
            output.complete("Search")
            output.emit()
            raise click.ClickException("Search failed")

        # 2. Search for endpoints
        output.action(f"Searching for: '{keywords}'")
        matches = _search_endpoints(spec, keywords, output)

        # 3. Process and display results
        total_matches = len(matches)
        display_count = min(total_matches, DISPLAY_LIMIT)

        # Add search statistics
        keyword_list = [k for k in keywords.split() if k]
        output.result(f"Search stats: {len(keyword_list)} keyword(s), {total_matches} result(s)")

        # Assess search quality
        quality = _get_search_quality(total_matches, display_count)
        output.note(f"Search quality: {quality}")

        if total_matches == 0:
            output.result("No matching endpoints found")
            output.note("Try different keywords or check the specification")
        else:
            # Enhanced result count display
            if display_count < total_matches:
                output.result(f"Found {total_matches} matching endpoint(s) - showing first {display_count}")
                # Only show broad search warning when significantly over limit
                if total_matches > DISPLAY_LIMIT * 2:
                    output.note(f"Keyword '{keywords}' is too broad. Try more specific terms.")
            else:
                output.result(f"Found {total_matches} matching endpoint(s)")

            # Add visual separator
            output.raw("---")

            # Display matching results
            for i, match in enumerate(matches[:display_count], 1):
                display_parts = [f"{match['path']}:{match['method']}"]

                if match["summary"]:
                    summary = match["summary"]
                    # Slightly longer limit since we have more space
                    if len(summary) > 80:
                        summary = summary[:77] + "..."
                    display_parts.append(f"- {summary}")

                output.raw(" ".join(display_parts))

            # Add visual separator
            output.raw("---")

            # Provide guidance based on result count
            if total_matches > DISPLAY_LIMIT:
                hidden_count = total_matches - DISPLAY_LIMIT
                output.note(f"{hidden_count} more matches not shown")

                # Suggest narrowing strategies
                output.action("Suggestions to narrow search")
                if "summary" in matches[0] and matches[0]["summary"]:
                    # Extract common terms from first few results
                    sample_summaries = [m["summary"].lower() for m in matches[:5] if m["summary"]]
                    if sample_summaries:
                        output.note("Review displayed results for more specific keywords")
                output.note(f"Use 'apiscope search {name} \"more specific terms\"' to narrow")

        # 4. Provide guidance for next steps
        if total_matches > 0:
            output.action("Next steps")
            if total_matches == 1:
                # Provide concrete example for single result
                example = f"{matches[0]['path']}:{matches[0]['method']}"
                output.note(f"Use 'apiscope describe {name} {example}' for details")
            elif total_matches <= DISPLAY_LIMIT:
                # All results visible
                output.note(f"All results visible. Use 'apiscope describe {name} <path:method>' for details")
            else:
                # Some results hidden
                output.note(f"Use 'apiscope describe {name} <path:method>' for endpoint details")
                output.note(f"Or refine search to see more relevant results")

        output.complete("Search")

    except Exception as e:
        output.error(f"Unexpected error during search: {e}")
        output.complete("Search")
        output.emit()
        raise click.ClickException("Search failed")

    output.emit()
