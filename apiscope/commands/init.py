# apiscope/commands/init.py

"""
Initialize apiscope configuration for the current project.
Uses LogLight-style output for consistent, concise logging.
"""

import click
from ..core.output import OutputBuilder
from ..core.config import (
    ConfigState,
    ensure_gitignore,
    save_config,
    SECTION_NAME
)

EXAMPLE_CONFIG = """# Example API specifications
# Format: <name> = <source>
#
# Sources can be:
# - Local file: ./api/openapi.yaml
# - Remote URL: https://api.example.com/openapi.json
#
# Uncomment and modify the lines below:
# stripe = https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.yaml
# github = https://github.com/github/rest-api-description/raw/main/descriptions/api.github.com/api.github.com.json
# petstore = https://petstore3.swagger.io/api/v3/openapi.json
"""

@click.command()
@click.pass_context
def init_command(ctx: click.Context) -> None:
    """
    Initialize apiscope configuration.

    Creates the configuration file (apiscope.ini) and cache directory
    (.apiscope/), and ensures the cache directory is ignored by git.
    """
    config_state: ConfigState = ctx.obj
    output = OutputBuilder()

    output.section("Initialization")

    # Check if already initialized
    if config_state.is_initialized:
        output.action("Checking existing configuration")
        output.result(f"Configuration already exists: {config_state.config_path}")
        output.complete("Initialization")
        output.emit()
        return

    # Ensure the specs section exists
    output.action("Setting up configuration structure")
    if SECTION_NAME not in config_state.config_parser:
        config_state.config_parser[SECTION_NAME] = {}

    # Write example configuration if file doesn't exist or is empty
    if not config_state.config_path.exists() or config_state.config_path.stat().st_size == 0:
        config_state.config_path.write_text(EXAMPLE_CONFIG)
        config_state.config_parser.read(config_state.config_path)
        output.result(f"Created example configuration: {config_state.config_path}")
    else:
        # File exists with content, just ensure the section exists
        config_state.config_parser.read(config_state.config_path)
        if SECTION_NAME not in config_state.config_parser:
            config_state.config_parser[SECTION_NAME] = {}
        output.result(f"Updated existing configuration: {config_state.config_path}")

    # Update initialization state
    config_state.is_initialized = SECTION_NAME in config_state.config_parser

    # Ensure cache directory exists
    output.action("Creating cache directory")
    cache_dir = config_state.project_root / ".apiscope"
    cache_dir.mkdir(exist_ok=True)
    output.result(f"Cache directory: {cache_dir}")

    # Ensure .gitignore includes cache directory
    output.action("Updating version control ignore")
    try:
        ensure_gitignore(config_state)
        output.result("Updated .gitignore")
    except Exception as e:
        output.note(f"Could not update .gitignore: {e}")

    # Save configuration
    output.action("Saving configuration")
    try:
        save_config(config_state)
        output.result("Configuration saved successfully")
    except Exception as e:
        output.error(f"Failed to save configuration: {e}")
        raise click.ClickException("Configuration save failed")

    output.complete("Initialization")

    # Next steps guidance
    output.action("Next steps")
    output.note("Edit apiscope.ini to add API specifications")
    output.note("Run 'apiscope list' to view configured APIs")

    output.emit()
