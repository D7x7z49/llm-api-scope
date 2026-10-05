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
    "sync.help.argument.selector": "choose one of all, filesystem, repo, openapi, rfc, or llmstxt",
    "sync.help.argument.name": "narrow the range to one source name",
    "sync.help.option.force": "refresh selected sources regardless of freshness",
    "sync.error.runtime_context_unavailable": "runtime context is unavailable",
    "sync.error.invalid_options": "invalid sync options",
    "sync.error.preflight.git_missing": "cannot sync {target} because the Git executable is not available",
    "sync.error.invalid_selector": "sync selector {selector} is invalid. choose all or a supported document type",
    "sync.error.selector_conflict": "source name {name} does not match selector {selector}",
    "sync.error.name_not_found": "source {name} does not exist",
    "sync.error.parse_failed": "cannot parse source {source} because its location is invalid",
    "sync.error.source.parse.source_empty": "cannot parse source {source} because the source is empty",
    "sync.error.source.parse.source_whitespace": ("cannot parse source {source} because it has surrounding whitespace"),
    "sync.error.source.parse.path_home_unsupported": (
        "cannot parse source {source} because a home-relative path is not supported"
    ),
    "sync.error.source.parse.unsupported_scheme": (
        "cannot parse source {source} because scheme {scheme} is not supported"
    ),
    "sync.error.source.parse.remote_host_missing": (
        "cannot parse source {source} because the remote source has no host"
    ),
    "sync.error.source.parse.credentials_unsupported": (
        "cannot parse source {source} because source credentials are not supported"
    ),
    "sync.error.source.parse.fragments_unsupported": (
        "cannot parse source {source} because source fragments are not supported"
    ),
    "sync.error.source.parse.filesystem_path_required": (
        "cannot parse source {source} because a filesystem source must be a path"
    ),
    "sync.error.source.parse.filesystem_path_invalid": (
        "cannot parse source {source} because the filesystem path is invalid ({detail})"
    ),
    "sync.error.source.parse.location_invalid": (
        "cannot parse source {source} because the source location is invalid ({detail})"
    ),
    "sync.error.source.parse.ref_invalid": ("cannot parse source {source} because the repository ref is invalid"),
    "sync.error.source.parse.subpath_invalid": (
        "cannot parse source {source} because the repository path is invalid ({detail})"
    ),
    "sync.error.source.parse.rfc_number_invalid": (
        "cannot parse source {source} because an RFC source must be a decimal number ({number})"
    ),
    "sync.error.source.parse.local_form_unsupported": (
        "cannot parse source {source} because this document type has no local form"
    ),
    "sync.error.source.parse.scp_unsupported": (
        "cannot parse source {source} because an scp-style location is not supported"
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
    "sync.error.fetch.git_missing": "cannot fetch source {source} because the Git executable is not available",
    "sync.error.fetch.repo_clone_failed": "cannot fetch source {source} because Git clone failed",
    "sync.error.fetch.repo_clone_failed_detail": (
        "cannot fetch source {source} because Git reported a clone failure with {detail}"
    ),
    "sync.error.fetch.repo_ref_failed": (
        "cannot fetch source {source} because Git could not check out ref {ref} ({detail})"
    ),
    "sync.error.fetch.repo_path_failed": (
        "cannot fetch source {source} because Git could not select path {path} ({detail})"
    ),
    "sync.error.fetch.repo_path_missing": (
        "cannot fetch source {source} because the repository path {path} does not exist"
    ),
    "sync.error.fetch.transport_failed": ("cannot fetch source {source} because the transport reported {detail}"),
    "sync.error.cache_failed": "cannot update cache for {name} because the cache operation failed",
    "sync.error.partial_failed": "sync failed for {failed} of {total} selected sources",
}
