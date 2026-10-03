# apiscope/sync/_lib/repo/constants.py
from typing import Final

# ==============================================================================
# git
# ==============================================================================


GIT_COMMAND: Final = "git"
GH_COMMAND: Final = "gh"
GIT_TIMEOUT_SECONDS: Final = 120.0
GIT_PROXY_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})
