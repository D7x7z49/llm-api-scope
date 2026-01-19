# apiscope/commands/list.py

"""
List all configured API specifications.
Uses LogLight-style output for consistent, concise logging.
"""

import click
from typing import Tuple
from ..core.output import OutputBuilder
from ..core.config import ConfigState, get_specs

def _classify_source(source: str) -> Tuple[str, str]:
    """
    Classify source string into type and clean version.

    Args:
        source: Raw source string from configuration

    Returns:
        Tuple of (type, cleaned_source)
        Type is one of: URL, FILE, INVALID
    """
    cleaned = source.strip().strip('"\'')

    if cleaned.startswith(("http://", "https://")):
        return "URL", cleaned
    elif cleaned.startswith("./") or cleaned.startswith("../"):
        return "FILE", cleaned
    else:
        return "INVALID", cleaned

@click.command()
@click.pass_context
def list_command(ctx: click.Context) -> None:
    """
    List all configured API specifications.

    Displays each specification with its type and source.
    Provides guidance for invalid formats.
    """
    config_state: ConfigState = ctx.obj
    output = OutputBuilder()

    output.section("Listing API Specifications")

    # Check if configuration is initialized
    if not config_state.is_initialized:
        output.action("Checking configuration state")
        output.note("Configuration not initialized")
        output.note("Run 'apiscope init' first")
        output.complete("Listing API Specifications")
        output.emit()
        return

    try:
        # Get all configured specifications
        output.action("Reading configuration")
        specs = get_specs(config_state)
        output.result(f"Configuration file: {config_state.config_path}")

        if not specs:
            output.action("Checking configured APIs")
            output.note("No API specifications found")

            output.action("Configuration format")
            output.note("Add lines to apiscope.ini: <name> = <source>")
            output.note("Source types: URL (http://...), FILE (./... or ../...)")

            output.complete("Listing API Specifications")
            output.emit()
            return

        # Display found specifications
        output.action(f"Found {len(specs)} API specification(s)")

        has_invalid = False

        for name, source in specs.items():
            source_type, cleaned_source = _classify_source(source)

            # Format for display - truncate long sources
            display_source = cleaned_source
            if len(cleaned_source) > 60:
                display_source = cleaned_source[:57] + "..."

            # Choose marker based on type
            if source_type == "INVALID":
                output.note(f"{name} ({source_type}): {display_source}")
                has_invalid = True
            else:
                output.result(f"{name} ({source_type}): {display_source}")

        # Provide guidance for invalid entries
        if has_invalid:
            output.action("Format guidance for invalid entries")
            output.note("Use ./ or ../ for local files")
            output.note("Use http:// or https:// for URLs")

        output.complete("Listing API Specifications")

    except Exception as e:
        output.error(f"Failed to read configuration: {e}")
        output.complete("Listing API Specifications")
        output.emit()
        raise click.ClickException("Listing failed")

    output.emit()
