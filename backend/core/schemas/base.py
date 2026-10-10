"""
Base Pydantic schemas for Legatio AI.

All JSONB payloads must include a `version` field for forward compatibility,
as specified in 03-DATA-MODEL.md Section 4.5.
"""

from pydantic import BaseModel, ConfigDict


class VersionedSchema(BaseModel):
    """
    Base schema that includes a version field.

    All JSONB payloads stored in the database must inherit from this
    to ensure forward compatibility when the schema evolves.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )

    version: int = 1
