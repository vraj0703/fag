from typing import Optional, List

from pydantic import BaseModel, Field

from models.logical_unit import LogicalUnit


class DartFileAnalysis(BaseModel):
    """The main schema for the entire file analysis."""
    file_purpose: str = Field(description="A high-level summary of the entire file's role and functionality.")
    logical_units: Optional[List[LogicalUnit]] = Field(description="A list of all logical units found in the file.")
