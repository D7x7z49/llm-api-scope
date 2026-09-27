# apiscope/read_lib/schema.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from apiscope.read_lib.constants import INVARIANT_MESSAGES, OUTPUT_TEMPLATES, ReadInvariant, ReadOutput

ReadKind = Literal["text", "markdown", "binary"]
ReadRetrieval = Literal["cache", "network"]


@dataclass(frozen=True, slots=True)
class ReadResult:
    target: str
    kind: ReadKind
    content: str | None = None
    media_type: str | None = None
    encoding: str | None = None
    size: int | None = None
    retrieval: ReadRetrieval = "cache"

    def __post_init__(self) -> None:
        if self.kind in {"text", "markdown"} and self.content is None:
            raise ValueError(INVARIANT_MESSAGES[ReadInvariant.TEXT_CONTENT_REQUIRED])
        if self.kind == "binary" and self.size is None:
            raise ValueError(INVARIANT_MESSAGES[ReadInvariant.BINARY_SIZE_REQUIRED])

    def as_data(self) -> list[dict[str, Any]]:
        if self.kind in {"text", "markdown"}:
            return [
                {
                    "kind": self.kind,
                    "content": self.content,
                    "media_type": self.media_type,
                    "encoding": self.encoding,
                }
            ]
        return [{"kind": "binary", "size": self.size, "media_type": self.media_type}]

    def render_body(self) -> str:
        if self.kind in {"text", "markdown"}:
            return self.content or ""
        return OUTPUT_TEMPLATES[ReadOutput.BINARY_CONTENT_OMITTED].format(size=self.size)

    def as_extra(self, cache_state: str) -> dict[str, object]:
        extra: dict[str, object] = {"cache": cache_state, "kind": self.kind}
        if self.retrieval == "network":
            extra["retrieval"] = self.retrieval
        if self.media_type is not None:
            extra["media_type"] = self.media_type
        if self.encoding is not None:
            extra["encoding"] = self.encoding
        if self.size is not None:
            extra["size"] = self.size
        return extra
