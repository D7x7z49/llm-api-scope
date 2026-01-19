# apiscope/commands/list.py
"""
List all configured API specifications.
Uses LogLight-style output for consistent, concise logging.
"""
import click
from ..core.output import OutputBuilder
from ..core.config import GLOBAL_CONFIG

@click.command()
def list_command():
    """
    List all configured API specifications.

    Displays each specification with its type and source.
    Provides guidance for invalid formats.
    """
    output = OutputBuilder()
    output.section("Listing API Specifications")

    # Check if configuration is initialized
    if not GLOBAL_CONFIG.is_initialized:
        output.action("Checking configuration state")
        output.note("Configuration not initialized")
        output.note("Run 'apiscope init' first")
        output.complete("Listing API Specifications")
        output.emit()
        return

    try:
        # Get all configured specifications (already classified)
        output.action("Reading configuration")
        specs = GLOBAL_CONFIG.get_classified_specs()
        output.result(f"Configuration file: {GLOBAL_CONFIG.file}")

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

        has_unknown = False

        for name, (spec_type, cleaned_source) in specs.items():
            # Format for display - truncate long sources
            display_source = cleaned_source
            if len(cleaned_source) > 60:
                display_source = cleaned_source[:57] + "..."

            # Choose marker based on type
            if spec_type == "UNKNOWN":
                output.note(f"{name}, {spec_type}, {display_source}")
                has_unknown = True
            else:
                output.result(f"{name}, {spec_type}, {display_source}")

        # Provide guidance for unknown entries
        if has_unknown:
            output.action("Format guidance for unknown entries")
            output.note("Use ./ or ../ for local files")
            output.note("Use http:// or https:// for URLs")

        output.complete("Listing API Specifications")

    except Exception as e:
        output.error(f"Failed to read configuration: {e}")
        output.complete("Listing API Specifications")
        output.emit()
        raise click.ClickException("Listing failed")

    output.emit()
