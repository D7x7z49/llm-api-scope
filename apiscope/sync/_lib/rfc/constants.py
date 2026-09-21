# apiscope/sync/_lib/rfc/constants.py
from typing import Final

from apiscope.schema import DocumentType

# ==============================================================================
# source
# ==============================================================================


REMOTE_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})
SOURCE_TYPE: Final[DocumentType] = "rfc"
