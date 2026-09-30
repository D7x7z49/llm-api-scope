# apiscope/constants.py

from enum import StrEnum
from typing import Final

# ===============================================================================
# environment
# ===============================================================================

APISCOPE_HOME_ENV: Final = "APISCOPE_HOME"

# ===============================================================================
# application
# ===============================================================================

APP_NAME: Final = "apiscope"

# ===============================================================================
# application layout
# ===============================================================================

APP_DIRECTORY: Final = f".{APP_NAME}"
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

APISCOPE_IGNORE_RULE: Final = f"{APP_DIRECTORY}/"

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

# ==============================================================================
# report invariants
# ==============================================================================


class ReportInvariant(StrEnum):
    STATUS_INVALID = "root.report.status_invalid"
    SCOPE_INVALID = "root.report.scope_invalid"
    ACTION_INVALID = "root.report.action_invalid"
    META_NOT_MAPPING = "root.report.meta_not_mapping"
    CODE_INVALID = "root.report.code_invalid"
    SUCCESS_WITH_CODE = "root.report.success_with_code"
    SUCCESS_WITH_MESSAGE = "root.report.success_with_message"
    ERROR_WITHOUT_CODE = "root.report.error_without_code"
    DATA_NOT_LIST = "root.report.data_not_list"
    EXTRA_NOT_MAPPING = "root.report.extra_not_mapping"
    DATA_EXTRA_PAIR = "root.report.data_extra_pair"
    ERROR_WITH_DATA = "root.report.error_with_data"
    FIELD_NAME_UNSAFE = "root.report.field_name_unsafe"


REPORT_INVARIANT_MESSAGES: Final[dict[str, str]] = {
    ReportInvariant.STATUS_INVALID: "report status must be ok or error",
    ReportInvariant.SCOPE_INVALID: "report scope must be home or project",
    ReportInvariant.ACTION_INVALID: "report action must be a safe non-empty token",
    ReportInvariant.META_NOT_MAPPING: "report meta must be a mapping",
    ReportInvariant.CODE_INVALID: "report code must be a safe non-empty token",
    ReportInvariant.SUCCESS_WITH_CODE: "successful reports cannot contain a code",
    ReportInvariant.SUCCESS_WITH_MESSAGE: "successful reports cannot contain a message",
    ReportInvariant.ERROR_WITHOUT_CODE: "error reports require a code",
    ReportInvariant.DATA_NOT_LIST: "report data must be a list",
    ReportInvariant.EXTRA_NOT_MAPPING: "report extra must be a mapping",
    ReportInvariant.DATA_EXTRA_PAIR: "report data and extra must be provided together",
    ReportInvariant.ERROR_WITH_DATA: "error reports cannot contain read data",
    ReportInvariant.FIELD_NAME_UNSAFE: "report field name is unsafe {name!r}",
}
