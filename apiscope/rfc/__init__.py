# apiscope/rfc/__init__.py

from apiscope.rfc.app import app as rfc_app
from apiscope.rfc.app import check_deps as check_rfc_deps

__all__ = ["rfc_app", "check_rfc_deps"]
