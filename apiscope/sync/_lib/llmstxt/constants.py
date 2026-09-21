# apiscope/sync/_lib/llmstxt/constants.py
from typing import Final

from apiscope.schema import DocumentType

# ==============================================================================
# source
# ==============================================================================


REMOTE_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})
SOURCE_TYPE: Final[DocumentType] = "llmstxt"
