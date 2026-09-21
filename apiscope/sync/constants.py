# apiscope/sync/constants.py
from typing import Final

# ==============================================================================
# command
# ==============================================================================


COMMAND_NAME: Final = "sync"

# ==============================================================================
# user-facing messages
# ==============================================================================


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "sync.help.command": "fetch registered sources into the cache",
    "sync.help.argument.name": "the source name; omit it to inspect the selected range",
    "sync.help.option.source_type": "limit the range to one source type",
    "sync.help.option.force": "refresh selected sources regardless of freshness",
    "sync.error.runtime_context_unavailable": "runtime context is unavailable",
    "sync.error.invalid_options": "invalid sync options",
    "sync.error.preflight.git_missing": "cannot sync {target} because the Git executable is not available",
    "sync.error.range_conflict": "source name {name} cannot be combined with --source-type",
    "sync.error.name_not_found": "source {name} does not exist",
    "sync.error.parse_failed": "cannot parse source {source} because the parser reported {reason}",
    "sync.error.parse.source_empty": "cannot parse source {source} because the source is empty",
    "sync.error.parse.unsupported_scheme": ("cannot parse source {source} because scheme {scheme} is not supported"),
    "sync.error.parse.remote_host_missing": ("cannot parse source {source} because the remote source has no host"),
    "sync.error.parse.credentials_unsupported": (
        "cannot parse source {source} because source credentials are not supported"
    ),
    "sync.error.parse.fragments_unsupported": (
        "cannot parse source {source} because source fragments are not supported"
    ),
    "sync.error.parse.filesystem_path_required": (
        "cannot parse source {source} because a filesystem source must be a path"
    ),
    "sync.error.parse.filesystem_path_invalid": (
        "cannot parse source {source} because the filesystem path is invalid ({detail})"
    ),
    "sync.error.parse.location_invalid": (
        "cannot parse source {source} because the source location is invalid ({detail})"
    ),
    "sync.error.fetch_failed": "cannot fetch source {source} because the fetcher reported {reason}",
    "sync.error.fetch.filesystem_local_required": (
        "cannot fetch source {source} because a filesystem source must be local"
    ),
    "sync.error.fetch.filesystem_copy_failed": (
        "cannot fetch source {source} because copying the filesystem source failed with {detail}"
    ),
    "sync.error.fetch.source_path_missing": ("cannot fetch source {source} because the path {path} does not exist"),
    "sync.error.fetch.repo_location_invalid": (
        "cannot fetch source {source} because the repository location is invalid"
    ),
    "sync.error.fetch.repo_proxy_unsupported": (
        "cannot fetch source {source} because an HTTP proxy is not supported for repository scheme {scheme}"
    ),
    "sync.error.fetch.git_missing": "cannot fetch source {source} because the Git executable is not available",
    "sync.error.fetch.repo_clone_failed": "cannot fetch source {source} because Git clone failed",
    "sync.error.fetch.repo_clone_failed_detail": (
        "cannot fetch source {source} because Git reported a clone failure with {detail}"
    ),
    "sync.error.fetch.transport_failed": ("cannot fetch source {source} because the transport reported {detail}"),
    "sync.error.cache_failed": "cannot update cache for {name} because the cache operation failed",
    "sync.error.partial_failed": "sync failed for {failed} of {total} selected sources",
}
