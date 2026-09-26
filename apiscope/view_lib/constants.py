# apiscope/view_lib/constants.py
from enum import StrEnum
from typing import Final


class ProjectionReason(StrEnum):
    CONTENT_INVALID = "view_lib.projection.content_invalid"
    DOCUMENT_INVALID = "view_lib.projection.document_invalid"
    PATH_INVALID = "view_lib.projection.path_invalid"
    PATH_NOT_FOUND = "view_lib.projection.path_not_found"
    PATH_AMBIGUOUS = "view_lib.projection.path_ambiguous"
    INDEX_NOT_FOUND = "view_lib.projection.index_not_found"


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    ProjectionReason.CONTENT_INVALID: "cached content is invalid",
    ProjectionReason.DOCUMENT_INVALID: "cached document is invalid",
    ProjectionReason.PATH_INVALID: "cannot view path {path} because the path is invalid",
    ProjectionReason.PATH_NOT_FOUND: (
        "route {path} does not exist. longest valid prefix: {prefix}. available routes: {routes_text}"
    ),
    ProjectionReason.PATH_AMBIGUOUS: (
        "route {path} matches multiple nodes below {prefix}. choose one by index: {routes_text}"
    ),
    ProjectionReason.INDEX_NOT_FOUND: "tree index {index} does not exist",
}

__all__ = ["MESSAGE_TEMPLATES", "ProjectionReason"]
