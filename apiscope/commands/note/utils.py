"""Public utility functions for the note command module."""
import hashlib
from pathlib import Path
from datetime import datetime

from ...core.config import GlobalConfig


def ensure_readme(config: GlobalConfig):
    """Ensure .apiscope/notes/README.md exists with default content."""
    from .constants import README_CONTENT

    notes_dir = config.home / "notes"
    readme_path = notes_dir / "README.md"
    if not readme_path.exists():
        notes_dir.mkdir(parents=True, exist_ok=True)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(README_CONTENT.strip() + "\n")


def clean_empty_notes(notes_dir: Path):
    """Remove empty note files that have no active lock."""
    if not notes_dir.exists():
        return

    lock_dir = notes_dir / ".lock"
    active_locks = set()
    if lock_dir.exists():
        for lock_file in lock_dir.glob("*.lock"):
            content = lock_file.read_text().strip()
            if content:
                timestamp = content.split('|')[0]
                active_locks.add(timestamp)

    for author_dir in notes_dir.iterdir():
        if not author_dir.is_dir() or author_dir.name.startswith('.'):
            continue
        for note_file in author_dir.glob("*.note.txt"):
            if note_file.stat().st_size == 0:
                stem = note_file.stem
                timestamp = stem.split('.')[0]
                if timestamp not in active_locks:
                    note_file.unlink()


def get_auth_lock_path(config, author: str) -> Path:
    """Get the path for auth lock file."""
    notes_dir = config.home / "notes"
    lock_dir = notes_dir / ".lock"
    author_hash = hashlib.sha256(author.encode()).hexdigest()[:16]
    return lock_dir / f"{author_hash}.auth.lock"


def get_auth_file_path(config, author: str) -> Path:
    """Get the path for auth.json file."""
    notes_dir = config.home / "notes"
    return notes_dir / author / "auth.json"
