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

def find_project_root() -> Optional[Path]:
    """
    Find project root by looking for .git directory AND apiscope.ini.
    Returns None if either is missing (e.g., before initialization).
    """
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir() and (parent / "apiscope.ini").is_file():
            return parent
    return None


class GlobalConfig:
    """
    Global configuration manager with lazy initialization.
    """

    _instance = None  # Singleton pattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        # Prevent re-initialization
        if getattr(self, '_initialized', False):
            return

        self._root: Optional[Path] = None
        self._home: Optional[Path] = None
        self._file: Optional[Path] = None
        self._cache: Optional[Path] = None
        self._settings: Optional[configparser.ConfigParser] = None
        self._specs_cache: Optional[Dict[str, Tuple[str, str]]] = None  # name -> (type, source)

        # Try to auto-discover, but don't fail if not found
        try:
            self.load()
        except RuntimeError:
            # Not initialized yet, that's okay
            pass

        self._initialized = True

    def _ensure_loaded(self) -> None:
        """Ensure configuration is loaded, or raise RuntimeError."""
        if self._settings is None:
            raise RuntimeError(
                "Configuration not loaded. Run 'apiscope init' first or call load() manually."
            )

    def load(self) -> None:
        """Load configuration from disk. Raises RuntimeError if not found."""
        root = find_project_root()
        if root is None:
            raise RuntimeError("Project root not found. Run 'apiscope init' first.")

        self._root = root
        self._home = self._root / ".apiscope"
        self._file = self._root / "apiscope.ini"
        self._cache = self._home / "cache"
        self._settings = self._load_settings(self._file)
        self._specs_cache = None  # Clear cache

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._settings = None
        self._specs_cache = None
        self.load()

    @staticmethod
    def _load_settings(path: Path) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(path)
        return config

    @staticmethod
    def _classify_source(source: str) -> Tuple[str, str]:
        """
        Classify source string into type and clean version.

        Args:
            source: Raw source string from configuration

        Returns:
            Tuple of (type, cleaned_source)
            Type is one of: URL, FILE, UNKNOWN
        """
        cleaned = source.strip().strip('"\'')

        if cleaned.startswith(("http://", "https://")):
            return "URL", cleaned
        elif cleaned.startswith("./") or cleaned.startswith("../"):
            return "FILE", cleaned
        else:
            return "UNKNOWN", cleaned

    def _refresh_specs_cache(self) -> None:
        """Refresh the cached classified specs."""
        if not self.settings.has_section(SECTION_NAME):
            self._specs_cache = {}
            return

        self._specs_cache = {}
        for name, source in self.settings[SECTION_NAME].items():
            self._specs_cache[name] = self._classify_source(source)

    # Public properties with lazy validation

    @property
    def root(self) -> Path:
        self._ensure_loaded()
        return self._root  # type: ignore

    @property
    def home(self) -> Path:
        self._ensure_loaded()
        return self._home  # type: ignore

    @property
    def file(self) -> Path:
        self._ensure_loaded()
        return self._file  # type: ignore

    @property
    def cache(self) -> Path:
        self._ensure_loaded()
        return self._cache  # type: ignore

    @property
    def http_cache_path(self) -> Path:
        """Path to HTTP cache database."""
        return self.cache / "http.db"

    @property
    def settings(self) -> configparser.ConfigParser:
        self._ensure_loaded()
        return self._settings  # type: ignore

    # Configuration operations

    def get_specs(self) -> Dict[str, str]:
        """Get all API specifications from configuration (raw)."""
        if not self.settings.has_section(SECTION_NAME):
            return {}
        return dict(self.settings[SECTION_NAME])

    def get_classified_specs(self) -> Dict[str, Tuple[str, str]]:
        """Get all API specifications with classification (type, cleaned_source)."""
        if self._specs_cache is None:
            self._refresh_specs_cache()
        return self._specs_cache or {}

    def add_spec(self, name: str, source: str) -> None:
        """Add a new API specification to configuration."""
        if not self.settings.has_section(SECTION_NAME):
            self.settings.add_section(SECTION_NAME)

        if name in self.settings[SECTION_NAME]:
            raise ValueError(f"Specification '{name}' already exists")

        self.settings[SECTION_NAME][name] = source
        self._specs_cache = None  # Clear cache
        self._save()

    def remove_spec(self, name: str) -> bool:
        """Remove an API specification from configuration."""
        if not self.settings.has_section(SECTION_NAME):
            return False

        removed = self.settings.remove_option(SECTION_NAME, name)
        if removed:
            self._specs_cache = None  # Clear cache
            self._save()
        return removed

    def ensure_section(self) -> None:
        """Ensure the [specs] section exists in configuration."""
        if not self.settings.has_section(SECTION_NAME):
            self.settings.add_section(SECTION_NAME)
            self._save()

    def ensure_gitignore(self) -> None:
        """Ensure .apiscope directory is in .gitignore."""
        gitignore_path = self.root / ".gitignore"
        ignore_line = ".apiscope/\n"

        if not gitignore_path.exists():
            gitignore_path.write_text(ignore_line)
            return

        content = gitignore_path.read_text()
        if ignore_line not in content:
            if content and not content.endswith('\n'):
                content += '\n'
            content += ignore_line
            gitignore_path.write_text(content)

    def _save(self) -> None:
        """Save current configuration to disk."""
        with open(self.file, 'w') as f:
            self.settings.write(f)

    @property
    def is_initialized(self) -> bool:
        """Check if configuration is fully initialized (has [specs] section)."""
        if self._settings is None:
            return False
        return self.settings.has_section(SECTION_NAME)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        if self._home:
            self._home.mkdir(exist_ok=True)
        if self._cache:
            self._cache.mkdir(exist_ok=True)


# Global singleton instance
# Note: This creates the instance but doesn't immediately load config
GLOBAL_CONFIG = GlobalConfig()
