import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from ..db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id: so.Mapped[uuid.UUID] = so.mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    owner_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("users.id"), index=True )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    memberships: so.Mapped[list["Membership"]] = so.relationship( "Membership", back_populates="project", cascade="all, delete-orphan" ) # type: ignore

    boards: so.Mapped[list["Board"]] = so.relationship( "Board", back_populates="project", cascade="all, delete-orphan" ) # type: ignore

