from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

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
    archived: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("The board name cannot be empty.")
        return value
    
    @field_validator("position")
    @classmethod
    def validate_position(cls, value):
        if value is not None and value < 0:
            raise ValueError("Position must be a non-negative integer.")
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