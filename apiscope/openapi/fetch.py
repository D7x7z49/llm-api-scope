# apiscope/openapi/fetch.py

import shutil
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

OPENAPI_EXTENSIONS = {".json", ".yaml", ".yml"}


def _cache_key(source: str) -> str:
    return sha256(source.encode()).hexdigest()


def _fetch_local(source: str, cache_dir: Path) -> Path:
    suffix = Path(source).suffix.lower()
    ext = suffix if suffix in OPENAPI_EXTENSIONS else ".json"
    cache_path = cache_dir / f"{_cache_key(source)}{ext}"

    if not cache_path.exists():
        src = Path(source).expanduser().resolve()
        shutil.copy2(src, cache_path)

    return cache_path


def _fetch_remote(url: str, cache_dir: Path) -> Path:
    path = unquote(urlparse(url).path).rstrip()
    suffix = Path(path).suffix.lower()
    ext = suffix if suffix in OPENAPI_EXTENSIONS else ".json"
    cache_path = cache_dir / f"{_cache_key(url)}{ext}"

    if not cache_path.exists():
        resp = httpx.get(url, follow_redirects=True)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)

    return cache_path


def fetch_openapi_spec(source: str, cache_dir: Path) -> Path:
    if "://" in source:
        return _fetch_remote(source, cache_dir)
    return _fetch_local(source, cache_dir)
