# apiscope/rfc/fetch.py

import subprocess
from pathlib import Path

from apiscope.rfc.schema import ContentFormat

# rsync module sources
RFC_RSYNC_HOST = "rsync.rfc-editor.org"
RFC_INDEX_MODULE = "rfcs-json-only"
RFC_CONTENT_MODULE = "rfcs"


def _do_rsync(src: str, dst: str) -> str | None:
    result = subprocess.run(
        ["rsync", "-az", "--delete", src, f"{dst}/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return result.stderr.strip()
    return None


def fetch_all_index_json(dst_dir: Path) -> str | None:
    return _do_rsync(f"{RFC_RSYNC_HOST}::{RFC_INDEX_MODULE}", str(dst_dir))


def fetch_content_by_number(number: int, dst_dir: Path, fmt: ContentFormat) -> str | None:
    filename = f"rfc{number}.{fmt}"
    return _do_rsync(f"{RFC_RSYNC_HOST}::{RFC_CONTENT_MODULE}/{filename}", str(dst_dir))
