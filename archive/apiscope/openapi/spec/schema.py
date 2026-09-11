# apiscope/openapi/spec/schema.py

from pydantic import BaseModel


class SpecCommandContext(BaseModel):
    global_flag: bool = False
