from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.models.task import TaskStatus, PriorityLevel

class TaskCreateSchema(BaseModel):
    name: str = Field(..., max_length=256)
    assignee_id: Optional[UUID] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    priority: Optional[PriorityLevel] = None
    position: Optional[int] = None
    archived: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Task name cannot be empty.")
        if len(value) > 256:
            raise ValueError("Task name cannot exceed 256 characters.")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None and len(value) > 512:
            raise ValueError("Task description cannot exceed 512 characters.")
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past.")
        return value


class TaskUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=256)
    position: Optional[int] = None
    archived: Optional[bool] = None
    status: Optional[TaskStatus] = None
    priority: Optional[PriorityLevel] = None
    board_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Task name cannot be empty.")
        if len(value) > 256:
            raise ValueError("Task name cannot exceed 256 characters.")
        return value
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None and len(value) > 512:
            raise ValueError("Task description cannot exceed 512 characters.")
        return value
    
    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past.")
        return value
class TaskResponseSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    board_id: UUID
    status: TaskStatus
    priority: PriorityLevel
    position: int
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True