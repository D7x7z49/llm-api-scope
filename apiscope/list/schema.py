# apiscope/list/schema.py

from typing import Literal

from apiscope.schema import DocumentType, StrictSchemaModel

ListSelector = Literal["all"] | DocumentType


class ListOptions(StrictSchemaModel):
    selector: ListSelector
