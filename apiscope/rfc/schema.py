# apiscope/rfc/schema.py

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

INFO_FIELD_ORDER: list[str] = [
    "title",
    "authors",
    "pub_status",
    "status",
    "pub_date",
    "source",
    "abstract",
    "page_count",
    "doi",
    "draft",
    "see_also",
    "errata_url",
    "obsoletes",
    "obsoleted_by",
    "updates",
    "updated_by",
]

ContentFormat = Literal["xml", "txt"]


class RfcStatus(str, Enum):
    PS = "PROPOSED STANDARD"
    DS = "DRAFT STANDARD"
    STD = "INTERNET STANDARD"
    BCP = "BEST CURRENT PRACTICE"
    INFO = "INFORMATIONAL"
    EXP = "EXPERIMENTAL"
    HIST = "HISTORIC"
    NOT_ISSUED = "NOT ISSUED"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, s: str) -> RfcStatus | None:
        key = s.strip().upper()
        for member in cls:
            if member.name == key or member.value == key:
                return member
        return None


class RfcMetadata(BaseModel):
    doc_id: str | None = None
    title: str | None = None
    authors: list[str] = []
    pub_status: RfcStatus | None = None
    status: RfcStatus | None = None
    pub_date: str | None = None
    abstract: str | None = None
    keywords: list[str] = []
    format: list[str] = []
    source: str | None = None
    page_count: str | None = None
    doi: str | None = None
    draft: str | None = None
    see_also: list[str] = []
    errata_url: str | None = None
    obsoletes: list[str] = []
    obsoleted_by: list[str] = []
    updates: list[str] = []
    updated_by: list[str] = []

    @classmethod
    def from_json_file(cls, path: Path) -> RfcMetadata:
        return cls.model_validate_json(path.read_text())

    def to_info_data(self) -> list[tuple[str, object]]:
        dumped = self.model_dump()
        return [(f, dumped[f]) for f in INFO_FIELD_ORDER]

    def is_format(self, fmt: str) -> bool:
        f = fmt.lower()
        return any(f == mf.lower() for mf in self.format)

    @property
    def is_xml_format(self) -> bool:
        return self.is_format("xml")

    @property
    def is_txt_format(self) -> bool:
        return (
            self.is_format("txt") or self.is_format("ascii") or not any(f for f in self.format if f)
        )


class RfcCommandContext(BaseModel):
    index_json_dir: Path
    content_xml_dir: Path
    content_txt_dir: Path

    def get_index_json_path(self, number: int) -> Path:
        return self.index_json_dir / f"rfc{number}.json"

    def get_content_xml_path(self, number: int) -> Path:
        return self.content_xml_dir / f"rfc{number}.xml"

    def get_content_txt_path(self, number: int) -> Path:
        return self.content_txt_dir / f"rfc{number}.txt"

    def get_index_json(self, number: int) -> RfcMetadata | None:
        path = self.get_index_json_path(number)
        if not path.exists():
            return None
        return RfcMetadata.from_json_file(path)

    def get_content_xml(self, number: int) -> str | None:
        path = self.get_content_xml_path(number)
        if not path.exists():
            return None
        return path.read_text()

    def get_content_txt(self, number: int) -> str | None:
        path = self.get_content_txt_path(number)
        if not path.exists():
            return None
        return path.read_text()
