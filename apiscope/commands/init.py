# apiscope/commands/init.py
"""
Initialize apiscope configuration for the current project.
Uses LogLight-style output for consistent, concise logging.
"""
import click
from pathlib import Path
from ..core.output import OutputBuilder
from ..core.config import find_project_root, GLOBAL_CONFIG

EXAMPLE_CONFIG = f"""[specs]
# Example API specifications
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

def _find_git_root() -> Path:
    """Find git root directory (for init command)."""
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return current  # Fallback to current directory

@click.command()
def init_command():
    """
    Initialize apiscope configuration.

    Creates the configuration file (apiscope.ini) and cache directory
    (.apiscope/), and ensures the cache directory is ignored by git.
    """
    output = OutputBuilder()
    output.section("Initialization")

    # 1. Check if already initialized
    output.action("Checking existing configuration")

    already_initialized = find_project_root() is not None
    if already_initialized:
        output.result("Configuration already initialized")
        output.note("Run 'apiscope list' to view configured APIs")
        output.complete("Initialization")
        output.emit()
        return

    # 2. Find git root for new initialization
    output.action("Finding project root")
    project_root = _find_git_root()
    output.result(f"Project root: {project_root}")

    # 3. Create directories
    output.action("Creating directory structure")

    home_dir = project_root / ".apiscope"
    cache_dir = home_dir / "cache"
    config_file = project_root / "apiscope.ini"

    home_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)

    output.result(f"Cache directory: {cache_dir}")

    # 4. Create configuration file with [specs] section
    output.action("Creating configuration file")

    if not config_file.exists():
        config_file.write_text(EXAMPLE_CONFIG)
        output.result(f"Created configuration: {config_file}")
    else:
        # File exists, ensure it has [specs] section
        output.result(f"Configuration exists: {config_file}")
        output.action("Ensuring [specs] section")
        try:
            GLOBAL_CONFIG._root = project_root
            GLOBAL_CONFIG._file = config_file
            GLOBAL_CONFIG._settings = GLOBAL_CONFIG._load_settings(config_file)
            GLOBAL_CONFIG.ensure_section()
            output.result("Added [specs] section")
        except Exception as e:
            output.note(f"Could not modify existing config: {e}")

    # 5. Update .gitignore
    output.action("Updating version control ignore")

    gitignore_path = project_root / ".gitignore"
    ignore_line = ".apiscope/\n"

    if not gitignore_path.exists():
        gitignore_path.write_text(ignore_line)
        output.result("Created .gitignore file")
    else:
        content = gitignore_path.read_text()
        if ignore_line not in content:
            if content and not content.endswith('\n'):
                content += '\n'
            content += ignore_line
            gitignore_path.write_text(content)
            output.result("Updated .gitignore")
        else:
            output.result(".gitignore already contains .apiscope/")

    # 6. Reload global config
    output.action("Reloading configuration")
    try:
        GLOBAL_CONFIG.reload()
        output.result("Configuration loaded successfully")
    except Exception as e:
        output.note(f"Could not reload configuration: {e}")
        output.note("Configuration will be available after restarting the tool")

    output.complete("Initialization")

    # 7. Next steps
    output.action("Next steps")
    output.note("Edit apiscope.ini to add API specifications")
    output.note("Run 'apiscope list' to view configured APIs")

    output.emit()
