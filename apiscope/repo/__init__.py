# apiscope/repo/__init__.py

from apiscope.repo.app import app as repo_app
from apiscope.repo.app import check_deps as check_repo_deps

__all__ = ["repo_app", "check_repo_deps"]
