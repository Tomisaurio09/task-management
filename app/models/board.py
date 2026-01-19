import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from ..db.session import Base

class Board(Base):
    __tablename__ = "boards"

    id: so.Mapped[uuid.UUID] = so.mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    project_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("projects.id") )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), index=True
    )
    updated_at : so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    position: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    project: so.Mapped["Project"] = so.relationship( "Project", back_populates="boards" ) # type: ignore
    tasks: so.Mapped[list["Task"]] = so.relationship( "Task", back_populates="board", cascade="all, delete-orphan" ) # type: ignore
