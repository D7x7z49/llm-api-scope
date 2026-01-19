# apiscope/core/config.py
"""
Configuration state management for apiscope.
Maintains a single source of truth for project configuration.
"""
import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration section name
SECTION_NAME = "specs"

@dataclass
class ConfigState:
    """Global configuration state container."""
    project_root: Path
    config_path: Path
    config_parser: configparser.ConfigParser
    is_initialized: bool = False

class ConfigurationError(Exception):
    """Raised when configuration operations fail."""
    pass

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Find project root by looking for .git directory or apiscope.ini.

    Args:
        start_path: Path to start searching from. If None, uses current directory.

    Returns:
        Path to project root.

    Raises:
        ConfigurationError: If no project root can be determined.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Check current and all parent directories
    for parent in [current] + list(current.parents):
        # Check for .git directory (common project marker)
        if (parent / ".git").is_dir():
            return parent

        # Check for apiscope.ini (our own config file)
        if (parent / "apiscope.ini").is_file():
            return parent

    # If we can't find a project root, use the directory containing apiscope.ini
    # or the current directory if no config exists yet
    config_path = current / "apiscope.ini"
    if config_path.exists():
        return config_path.parent

    # Default to current directory (will be initialized here)
    return current

def load_or_init_config(project_root: Optional[Path] = None) -> ConfigState:
    """
    Load existing configuration or initialize new one.

    Args:
        project_root: Explicit project root path. If None, will be discovered.

    Returns:
        Initialized ConfigState object.
    """
    if project_root is None:
        project_root = find_project_root()

    config_path = project_root / "apiscope.ini"
    config_parser = configparser.ConfigParser()

    # Initialize with default structure if file doesn't exist
    if not config_path.exists():
        config_parser[SECTION_NAME] = {}
        is_initialized = False
    else:
        config_parser.read(config_path)
        is_initialized = SECTION_NAME in config_parser

    return ConfigState(
        project_root=project_root,
        config_path=config_path,
        config_parser=config_parser,
        is_initialized=is_initialized
    )

def get_specs(state: ConfigState) -> Dict[str, str]:
    """
    Get all API specifications from configuration.

    Args:
        state: Current configuration state.

    Returns:
        Dictionary mapping spec names to source URLs/paths.

    Raises:
        ConfigurationError: If configuration is not properly initialized.
    """
    if not state.is_initialized:
        raise ConfigurationError(
            "Configuration not initialized. Run 'apiscope init' first."
        )

    return dict(state.config_parser[SECTION_NAME])

def save_config(state: ConfigState) -> None:
    """
    Save current configuration to disk.

    Args:
        state: Configuration state to save.

    Raises:
        ConfigurationError: If saving fails.
    """
    try:
        with open(state.config_path, 'w') as config_file:
            state.config_parser.write(config_file)
    except (IOError, OSError) as e:
        raise ConfigurationError(f"Failed to save configuration: {e}")

def add_spec(state: ConfigState, name: str, source: str) -> None:
    """
    Add a new API specification to configuration.

    Args:
        state: Current configuration state.
        name: Unique identifier for the specification.
        source: URL or file path to the OpenAPI specification.

    Raises:
        ConfigurationError: If spec with this name already exists.
    """
    if not state.is_initialized:
        # Initialize the section if needed
        state.config_parser[SECTION_NAME] = {}
        state.is_initialized = True

    if name in state.config_parser[SECTION_NAME]:
        raise ConfigurationError(
            f"Specification '{name}' already exists in configuration."
        )

    state.config_parser[SECTION_NAME][name] = source

def remove_spec(state: ConfigState, name: str) -> bool:
    """
    Remove an API specification from configuration.

    Args:
        state: Current configuration state.
        name: Name of the specification to remove.

    Returns:
        True if spec was removed, False if it didn't exist.
    """
    if not state.is_initialized or name not in state.config_parser[SECTION_NAME]:
        return False

    state.config_parser.remove_option(SECTION_NAME, name)
    return True

def get_cache_directory(state: ConfigState) -> Path:
    """
    Get path to cache directory for this project.

    Args:
        state: Current configuration state.

    Returns:
        Path to .apiscope cache directory.
    """
    cache_dir = state.project_root / ".apiscope"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir

def ensure_gitignore(state: ConfigState) -> None:
    """
    Ensure .apiscope directory is in .gitignore.

    Args:
        state: Current configuration state.
    """
    gitignore_path = state.project_root / ".gitignore"
    ignore_line = ".apiscope/\n"

    if not gitignore_path.exists():
        gitignore_path.write_text(ignore_line)
        return

    content = gitignore_path.read_text()
    if ignore_line not in content:
        # Add a newline if file doesn't end with one
        if content and not content.endswith('\n'):
            content += '\n'
        content += ignore_line
        gitignore_path.write_text(content)
