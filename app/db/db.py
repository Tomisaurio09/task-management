import sqlalchemy as sa
import sqlalchemy.orm as so
from enum import Enum
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import uuid
from sqlalchemy import Enum as SqlEnum
from datetime import datetime, timezone
"""
maybe I use bycript instead of hashing
from werkzeug.security import generate_password_hash, check_password_hash
"""
#future change: "postgresql://user:password@localhost:5432/mydb"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = sa.create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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



class Project(Base):
    __tablename__ = "projects"

    id: so.Mapped[uuid.UUID] = so.mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    owner_id: so.Mapped[uuid.UUID] = so.mapped_column( UUID(as_uuid=True), sa.ForeignKey("users.id") )
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=datetime.now(timezone.utc), index=True
    )
    memberships: so.Mapped[list["Memberships"]] = so.relationship( "Memberships", back_populates="project", cascade="all, delete-orphan" )

    boards: so.Mapped[list["Board"]] = so.relationship( "Board", back_populates="project", cascade="all, delete-orphan" )

class TaskStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class PriorityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


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
    position: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    project: so.Mapped["Project"] = so.relationship( "Project", back_populates="boards" )
    tasks: so.Mapped[list["Task"]] = so.relationship( "Task", back_populates="board", cascade="all, delete-orphan" )

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

    board: so.Mapped["Board"] = so.relationship( "Board", back_populates="tasks" )


class Memberships(Base):
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
    project: so.Mapped["Project"] = so.relationship( "Project", back_populates="memberships" )
    #Maybe adding this later if necessary
    #user: so.Mapped["User"] = so.relationship("User", back_populates="memberships")
