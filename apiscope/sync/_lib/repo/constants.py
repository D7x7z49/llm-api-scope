# apiscope/sync/_lib/repo/constants.py
from typing import Final

# ==============================================================================
# git
# ==============================================================================


GIT_COMMAND: Final = "git"
GH_COMMAND: Final = "gh"
GIT_TIMEOUT_SECONDS: Final = 120.0
GIT_PROXY_ENVIRONMENT_NAMES: Final[tuple[str, ...]] = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "GIT_PROXY_COMMAND",
)
GIT_PROXY_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})
