# apiscope/constants.py

from typing import Final

# ===============================================================================
# environment
# ===============================================================================

APISCOPE_HOME_ENV: Final = "APISCOPE_HOME"

# ===============================================================================
# application layout
# ===============================================================================

APP_DIRECTORY: Final = ".apiscope"
CACHE_DIRECTORY: Final = "cache"

# ===============================================================================
# configuration files
# ===============================================================================

CONFIG_FILENAME: Final = "config.json"
LOCAL_CONFIG_FILENAME: Final = "local.json"

# ===============================================================================
# schema assets
# ===============================================================================

SCHEMA_DIRECTORY: Final = "schema"
SCHEMA_FILENAME: Final = "config.schema.json"
LOCAL_CONFIG_SCHEMA_FILENAME: Final = "config.local.schema.json"
CONFIG_SCHEMA_REF: Final = f"./{SCHEMA_DIRECTORY}/{SCHEMA_FILENAME}"
LOCAL_CONFIG_SCHEMA_REF: Final = f"./{SCHEMA_DIRECTORY}/{LOCAL_CONFIG_SCHEMA_FILENAME}"

# ===============================================================================
# project files
# ===============================================================================

GITIGNORE_FILENAME: Final = ".gitignore"

# ===============================================================================
# project ignore policy
# ===============================================================================

APISCOPE_IGNORE_RULE: Final = ".apiscope/"

# ===============================================================================
# home layout version
# ===============================================================================

VERSION_FILENAME: Final = "VERSION"
HOME_LAYOUT_VERSION: Final = "1"
