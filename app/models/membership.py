import sqlalchemy as sa
import sqlalchemy.orm as so
from enum import Enum
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Enum as SqlEnum
from datetime import datetime, timezone
from ..db.db_session import Base


class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Membership(Base):
    __tablename__ = "memberships"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)      
    user_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("users.id") )
    project_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("projects.id") )
    role: so.Mapped[UserRole] = so.mapped_column(SqlEnum(UserRole), default=UserRole.VIEWER)
    joined_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), index=True
    )

    invited_by: so.Mapped[Optional[uuid.UUID]] = so.mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("user_id", "project_id", name="uq_membership_user_project"),
    )
    project: so.Mapped["Project"] = so.relationship( "Project", back_populates="memberships" ) # type: ignore
    #Maybe adding this later if necessary
    #user: so.Mapped["User"] = so.relationship("User", back_populates="memberships")
