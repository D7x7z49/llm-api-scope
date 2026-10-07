# apiscope/bookmark/prune/schema.py

from apiscope.schema import StrictSchemaModel


class PruneOptions(StrictSchemaModel):
    invalid: bool = False
