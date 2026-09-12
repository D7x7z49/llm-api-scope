# apiscope/constants.py

from typing import Final, Literal

# ===============================================================================
# environment and paths
# ===============================================================================

APISCOPE_HOME_ENV: Final = "APISCOPE_HOME"
APP_DIRECTORY: Final = ".apiscope"
CONFIG_FILENAME: Final = "config.json"
VERSION_FILENAME: Final = "VERSION"
CACHE_DIRECTORY: Final = "cache"

# ===============================================================================
# schema versions
# ===============================================================================

HOME_LAYOUT_VERSION: Final = "1"
CONFIG_VERSION: Final[Literal[1]] = 1
