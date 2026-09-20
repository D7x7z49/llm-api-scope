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
    "root.error.config.home_resolve_failed": "cannot resolve apiscope home {path}; check the path and its permissions",
    "root.error.config.read_failed": "cannot read {path}; check the file and its permissions",
    "root.error.config.write_failed": "cannot write {path}; check permissions and choose a writable location",
    "root.error.config.invalid": "invalid configuration in {path}; fix or remove it before retrying",
    "root.error.config.schema_generation_failed": "cannot generate schema for {path}",
    "root.error.config.unsupported_home_layout": (
        "unsupported home layout in {path}; keep the file unchanged and migrate it before retrying"
    ),
    "root.error.gitignore.not_file": "cannot use {path}; the path is not a file",
    "root.error.gitignore.read_failed": "cannot read {path}; check the file and its permissions",
    "root.error.gitignore.write_failed": "cannot write {path}; check the file and its permissions",
    "root.error.preflight.project_inspection_failed": (
        "cannot inspect project path {location}; check the path and its permissions"
    ),
    "root.error.preflight.directory_prepare_failed": (
        "cannot prepare directory {path}; check permissions and choose a writable location"
    ),
    "root.error.output.unsupported_format": "unsupported output format {format}",
    "root.error.output.missing_code": "error report has no code",
    "root.error.output.missing_template": "message template is missing for {code}",
    "root.error.output.template_render_failed": "message template cannot be rendered for {code}",
    "root.error.output.missing_message": "error report has no message for {code}",
    "root.error.output.write_sections": "write reports cannot contain text body or foot",
    "root.error.output.missing_extra": "read reports require extra data",
    "root.error.output.serialization_failed": "report contains a value that cannot be serialized",
    "root.error.errors.invalid_code": "error code must be a dotted lower-case key",
    "root.error.errors.invalid_values": "error values must be a mapping",
}
