# apiscope/read_lib/constants.py
from enum import StrEnum
from typing import Final


class ReadReason(StrEnum):
    CONTENT_INVALID = "read_lib.reader.content_invalid"
    READ_FAILED = "read_lib.reader.read_failed"
    READER_UNSUPPORTED = "read_lib.registry.reader_unsupported"
    TARGET_INVALID = "read_lib.reader.target_invalid"
    TARGET_NOT_FOUND = "read_lib.reader.target_not_found"
    TARGET_NOT_LEAF = "read_lib.reader.target_not_leaf"


class ReadOutput(StrEnum):
    BINARY_CONTENT_OMITTED = "read_lib.output.binary_content_omitted"


class ReadInvariant(StrEnum):
    BINARY_SIZE_REQUIRED = "read_lib.schema.binary_size_required"
    TEXT_CONTENT_REQUIRED = "read_lib.schema.text_content_required"


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    ReadReason.CONTENT_INVALID: "cached source content is invalid",
    ReadReason.READ_FAILED: "cannot read target {target}",
    ReadReason.READER_UNSUPPORTED: "source type {doc_type} has no registered reader",
    ReadReason.TARGET_INVALID: "target {target} is invalid",
    ReadReason.TARGET_NOT_FOUND: "target {target} does not exist in the source content",
    ReadReason.TARGET_NOT_LEAF: "{target} is an ordinary node, not a leaf",
}

OUTPUT_TEMPLATES: Final[dict[str, str]] = {
    ReadOutput.BINARY_CONTENT_OMITTED: "(binary content omitted; {size} bytes)",
}

INVARIANT_MESSAGES: Final[dict[str, str]] = {
    ReadInvariant.BINARY_SIZE_REQUIRED: "binary read results require a size",
    ReadInvariant.TEXT_CONTENT_REQUIRED: "text read results require content",
}

__all__ = [
    "INVARIANT_MESSAGES",
    "MESSAGE_TEMPLATES",
    "OUTPUT_TEMPLATES",
    "ReadInvariant",
    "ReadOutput",
    "ReadReason",
]
