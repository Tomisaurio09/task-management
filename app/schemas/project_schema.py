from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class ProjectCreateSchema(BaseModel):
    name: str = Field(..., max_length=128, description="Project name, max 128 characters")
    #owner_id: UUID

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("The project name cannot be empty.")
        return value


class ProjectUpdateSchema(BaseModel):
    # Campos opcionales para edición
    name: Optional[str] = Field(None, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("The project name cannot be empty.")
        return value


from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MembershipResponseSchema(BaseModel):
    id: int
    user_id: UUID
    project_id: UUID
    role: str
    joined_at: datetime
    invited_by: UUID | None

    class Config:
        from_attributes = True  # antes era orm_mode=True

class ProjectResponseSchema(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    memberships: list[MembershipResponseSchema] = []

    class Config:
        from_attributes = True
