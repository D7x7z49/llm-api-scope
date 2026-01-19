# apiscope/commands/list.py
"""
List all configured API specifications.
"""
import click
from ..core.config import ConfigState, get_specs

@click.command()
@click.pass_context
def list_command(ctx: click.Context) -> None:
    """
    List all configured API specifications.

    Displays each specification name and its source in a readable format.
    """
    config_state: ConfigState = ctx.obj

    # Check if configuration is initialized
    if not config_state.is_initialized:
        click.echo("Configuration not initialized. Run 'apiscope init' first.")
        return

    try:
        # Get all configured specifications
        specs = get_specs(config_state)

        if not specs:
            click.echo("No API specifications configured.")
            click.echo("\nTo add specifications:")
            click.echo("  1. Edit apiscope.ini in your project root")
            click.echo("  2. Add lines in the format: <name> = <source>")
            click.echo("  3. Sources can be local files or remote URLs")
            return

        # Display specifications in a clear format
        click.echo(f"Configured API specifications ({len(specs)} total):")
        click.echo()

        for name, source in specs.items():
            # Format source for display (truncate long URLs)
            display_source = source
            if len(source) > 60:
                display_source = source[:57] + "..."

            click.echo(f"  {click.style(name, fg='cyan', bold=True)}")
            click.echo(f"    Source: {display_source}")

            # Show source type hint
            if source.startswith(("http://", "https://")):
                click.echo("    Type: Remote URL")
            elif "/" in source or "\\" in source:
                click.echo("    Type: Local file")
            else:
                click.echo("    Type: Unknown (check format)")

            click.echo()

        # Show help text
        click.echo("Commands to use with these specifications:")
        click.echo(f"  {click.style('apiscope search <name> <keywords>', fg='green')}")
        click.echo(f"  {click.style('apiscope describe <name> <path:method>', fg='green')}")

    except Exception as e:
        raise click.ClickException(f"Failed to list specifications: {e}")
