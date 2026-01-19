# apiscope/commands/init.py
"""
Initialize apiscope configuration for the current project.
"""
import click
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

    # Check if already initialized
    if config_state.is_initialized:
        click.echo(
            f"Configuration already initialized at: {config_state.config_path}"
        )
        return

    # Ensure the specs section exists
    if SECTION_NAME not in config_state.config_parser:
        config_state.config_parser[SECTION_NAME] = {}

    # Write example configuration if file doesn't exist or is empty
    if not config_state.config_path.exists() or config_state.config_path.stat().st_size == 0:
        config_state.config_path.write_text(EXAMPLE_CONFIG)
        config_state.config_parser.read(config_state.config_path)
        click.echo(f"Created example configuration at: {config_state.config_path}")
    else:
        # File exists with content, just ensure the section exists
        config_state.config_parser.read(config_state.config_path)
        if SECTION_NAME not in config_state.config_parser:
            config_state.config_parser[SECTION_NAME] = {}
        click.echo(f"Updated existing configuration at: {config_state.config_path}")

    # Update initialization state
    config_state.is_initialized = SECTION_NAME in config_state.config_parser

    # Ensure cache directory exists
    cache_dir = config_state.project_root / ".apiscope"
    cache_dir.mkdir(exist_ok=True)
    click.echo(f"Created cache directory at: {cache_dir}")

    # Ensure .gitignore includes cache directory
    try:
        ensure_gitignore(config_state)
        click.echo("Updated .gitignore to include .apiscope/")
    except Exception as e:
        click.echo(f"Warning: Could not update .gitignore: {e}")

    # Save configuration
    try:
        save_config(config_state)
        click.echo("Configuration initialized successfully.")
        click.echo("\nNext steps:")
        click.echo("  1. Edit apiscope.ini to add your API specifications")
        click.echo("  2. Run 'apiscope list' to see configured APIs")
        click.echo("  3. Run 'apiscope search <name> <keywords>' to search endpoints")
    except Exception as e:
        raise click.ClickException(f"Failed to save configuration: {e}")
