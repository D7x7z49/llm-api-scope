# apiscope/repo/__init__.py

from apiscope.repo.app import app as repo_app
from apiscope.repo.app import check_deps as check_repo_deps

__all__ = ["check_repo_deps", "repo_app"]
