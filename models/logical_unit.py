from typing import Optional, Literal, List

from pydantic import BaseModel, Field


class LogicalUnit(BaseModel):
    """Defines the structure for a single logical code unit."""
    name: Optional[str] = Field(description="The name of the class, function, enum, etc.")
    type: Optional[Literal[
        'class', 'abstract class', 'enum', 'interface', 'function', 'parameter', 'method', 'library',
        'exception', 'extension method', 'private method', 'field', 'typedef']]
    purpose: Optional[str] = Field(description="A concise summary of the unit's purpose.")
    dependencies: List[str] = Field(default_factory=list,
                                    description="A list of other units or libraries this unit depends on.")
    returnType: Optional[str] = Field(None, description="The unit's return type, if applicable.")
