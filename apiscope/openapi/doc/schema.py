# apiscope/openapi/doc/schema.py

from pydantic import BaseModel


class DocCommandContext(BaseModel):
    global_flag: bool = False
