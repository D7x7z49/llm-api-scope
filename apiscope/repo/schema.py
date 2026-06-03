# apiscope/repo/schema.py

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from apiscope.config import RepoConfig


class RepoEntry(BaseModel):
    url: str
    dir: str
    target: str

    def __hash__(self) -> int:
        return hash(self.sha256_id)

    @property
    def sha256_id(self) -> str:
        return hashlib.sha256(self.url.encode()).hexdigest()

    @property
    def reference(self) -> tuple[str, str] | None:
        if self.target.startswith("branch:"):
            return "branch", self.target[len("branch:") :]
        elif self.target.startswith("tag:"):
            return "tag", self.target[len("tag:") :]
        elif self.target.startswith("commit:"):
            return "commit", self.target[len("commit:") :]
        else:
            return None

    @classmethod
    def from_config(cls, config: "RepoConfig") -> set["RepoEntry"]:
        return {cls(url=url, dir=ec.dir, target=ec.target) for url, ec in config.entries.items()}


# ==============================================================================
# context
# ==============================================================================


class RepoCommandContext(BaseModel):
    # computed properties
    cache_dir: Path
    tmp_dir: Path

    # sub command options
    global_flag: bool
