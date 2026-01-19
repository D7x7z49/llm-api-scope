# apiscope/core/parser.py

"""
OpenAPI specification parser.
"""

# Standard library
import hashlib
import json
from io import StringIO
from pathlib import Path
from typing import Optional, Tuple
import time

# Third-party libraries
import httpx
from openapi_core import OpenAPI

# Local modules
from .config import GLOBAL_CONFIG


# Constants
DEFAULT_CACHE_TTL = 24 * 3600  # 24 hours in seconds
INVALID_SOURCE_MESSAGE = (
    "Use http(s):// for URLs or ./path for local files."
)


class ParserError(Exception):
    """Parser-specific errors."""
    pass


def _get_cache_key(url: str) -> str:
    """Generate cache key from URL."""
    return hashlib.md5(url.encode()).hexdigest()


def _get_cache_path(url: str) -> Path:
    """Get cache file path for URL."""
    cache_key = _get_cache_key(url)
    return GLOBAL_CONFIG.cache / "http" / cache_key


def _is_cache_valid(
    file_path: Path,
    max_age_seconds: int = DEFAULT_CACHE_TTL
) -> Tuple[bool, Optional[float]]:
    """
    Check if a file cache is valid based on modification time.

    Args:
        file_path: Path to the cache file.
        max_age_seconds: Maximum age in seconds before cache is considered stale.

    Returns:
        Tuple of (is_valid, modification_time).
        modification_time is None if file doesn't exist.
    """
    if not file_path.exists():
        return False, None

    try:
        mtime = file_path.stat().st_mtime
        is_valid = (time.time() - mtime) < max_age_seconds
        return is_valid, mtime
    except OSError:
        return False, None


def _load_cache_content(cache_path: Path) -> Optional[str]:
    """
    Load content from cache file.

    Args:
        cache_path: Path to cache file.

    Returns:
        Cache content or None if cache is invalid or corrupted.
    """
    is_valid, _ = _is_cache_valid(cache_path)
    if not is_valid:
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        if isinstance(cache_data, dict) and 'content' in cache_data:
            return cache_data['content']
    except (json.JSONDecodeError, KeyError, IOError, TypeError):
        pass

    return None


def _save_cache_content(cache_path: Path, content: str) -> None:
    """Save content to cache file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        'timestamp': time.time(),
        'content': content
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False)


def _fallback_to_cache(cache_path: Path) -> Optional[OpenAPI]:
    """Attempt to load from cache as fallback."""
    cached_content = _load_cache_content(cache_path)
    if cached_content is None:
        return None

    try:
        with StringIO(cached_content) as f:
            return OpenAPI.from_file(f)
    except Exception:
        return None


def get_spec(name: str, force: bool = False) -> OpenAPI:
    """
    Get OpenAPI spec by name.

    Args:
        name: Configuration name of the spec.
        force: Bypass HTTP cache if True.

    Returns:
        OpenAPI object.

    Raises:
        ParserError: If specification cannot be loaded.
    """
    specs = GLOBAL_CONFIG.get_classified_specs()

    if name not in specs:
        available = ", ".join(specs.keys()) if specs else "none"
        raise ParserError(f"Spec '{name}' not found. Available: {available}")

    source_type, source = specs[name]

    if source_type == "UNKNOWN":
        raise ParserError(
            f"Invalid source for '{name}': {source}\n{INVALID_SOURCE_MESSAGE}"
        )

    try:
        if source_type == "URL":
            return _load_remote(source, force)
        else:  # FILE
            return _load_local(source)
    except ParserError:
        raise
    except Exception as e:
        raise ParserError(f"Failed to load '{name}': {e}")


def _load_remote(url: str, force: bool) -> OpenAPI:
    """Load remote spec with simple file caching."""
    cache_path = _get_cache_path(url)

    if not force:
        cached_content = _load_cache_content(cache_path)
        if cached_content is not None:
            with StringIO(cached_content) as f:
                return OpenAPI.from_file(f)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.text

            _save_cache_content(cache_path, content)

            with StringIO(content) as f:
                return OpenAPI.from_file(f)
    except (httpx.HTTPError, httpx.RequestError) as e:
        if not force:
            cached_spec = _fallback_to_cache(cache_path)
            if cached_spec is not None:
                return cached_spec
        raise ParserError(f"Failed to load from {url}: {e}")


def _load_local(source: str) -> OpenAPI:
    """Load local spec file."""
    file_path = (GLOBAL_CONFIG.root / source).resolve()
    return OpenAPI.from_path(file_path)
