import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from ..db.db_session import Base

class User(Base):
    __tablename__ = "users"

    id: so.Mapped[uuid.UUID] = so.mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    email: so.Mapped[str] = so.mapped_column(sa.String(128), unique=True, index=True)
    password: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    full_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    #Maybe adding this later if necessary
    #memberships: so.Mapped[list["Memberships"]] = so.relationship("Memberships", back_populates="user", cascade="all, delete-orphan")

