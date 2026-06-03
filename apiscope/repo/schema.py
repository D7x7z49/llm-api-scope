# apiscope/repo/schema.py

from pathlib import Path

from pydantic import BaseModel


class RepoCommandContext(BaseModel):
    cache_dir: Path
    tmp_dir: Path
