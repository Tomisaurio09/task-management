import sqlalchemy as sa
import sqlalchemy.orm as so
from enum import Enum
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Enum as SqlEnum
from datetime import datetime, timezone
from ..db.db_session import Base


class TaskStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class PriorityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: so.Mapped[uuid.UUID] = so.mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    status: so.Mapped[TaskStatus] = so.mapped_column(SqlEnum(TaskStatus), default=TaskStatus.ACTIVE)
    priority: so.Mapped[PriorityLevel] = so.mapped_column(SqlEnum(PriorityLevel), default=PriorityLevel.MEDIUM)
    board_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("boards.id") )
    assignee_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), index=True
    )
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(512), nullable=True)
    due_date: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, nullable=True)
    position: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    board: so.Mapped["Board"] = so.relationship( "Board", back_populates="tasks" ) # type: ignore

