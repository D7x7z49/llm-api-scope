# apiscope/rfc/schema.py

from pathlib import Path

from pydantic import BaseModel


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
