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

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "root.help.app": "read and cache structured documents from remote for LLM agents",
    "root.help.option.global": "use home configuration and skip project discovery",
    "root.help.option.json": "render reports as JSON",
    "root.error.config.home_resolve_failed": (
        "cannot resolve the apiscope home at {path} because the path is missing or inaccessible"
    ),
    "root.error.config.read_failed": "cannot read the file at {path} because it is missing or inaccessible",
    "root.error.config.write_failed": "cannot write the file at {path} because the path is not writable",
    "root.error.config.invalid": "configuration at {path} is invalid. fix or remove it before retrying",
    "root.error.config.schema_generation_failed": "cannot generate the schema at {path}",
    "root.error.config.unsupported_home_layout": (
        "cannot use the apiscope home at {path} because its layout is unsupported. "
        "keep the file unchanged and migrate it before retrying"
    ),
    "root.error.gitignore.not_file": "cannot use {path} because the path is not a file",
    "root.error.gitignore.read_failed": "cannot read the Git ignore file at {path} because it is inaccessible",
    "root.error.gitignore.write_failed": "cannot write the Git ignore file at {path} because it is not writable",
    "root.error.preflight.project_inspection_failed": (
        "cannot inspect the project at {location} because the path is missing or inaccessible"
    ),
    "root.error.preflight.directory_prepare_failed": (
        "cannot prepare the directory at {path} because it cannot be created or written"
    ),
    "root.error.output.unsupported_format": "output format {format} is not supported",
    "root.error.output.missing_code": "the error report is missing its code",
    "root.error.output.missing_template": "no message template exists for {code}",
    "root.error.output.template_render_failed": "cannot render the message template for {code}",
    "root.error.output.missing_message": "the error report for {code} is missing its message",
    "root.error.output.write_sections": "write reports cannot include body or foot sections",
    "root.error.output.missing_extra": "read reports require both data and extra sections",
    "root.error.output.serialization_failed": "report contains a value that cannot be serialized",
    "root.error.errors.invalid_code": "error codes must use dotted lower-case keys",
    "root.error.errors.invalid_values": "error values must be provided as a mapping",
}
