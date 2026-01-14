from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class BoardCreateSchema(BaseModel):
    name: str = Field(..., max_length=128)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("The board name cannot be empty.")
        return value

class BoardUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    position: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("The board name cannot be empty.")
        return value
    
class BoardResponseSchema(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    position: int
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True