# app/services/projects_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.membership import Membership, UserRole
from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from app.schemas.pagination import PaginatedResponse, PaginationParams, SortParams
from app.core.pagination import apply_sorting, paginate
from app.core.logger import logger
from sqlalchemy.orm import selectinload
from app.core.exceptions import (
    ProjectNotFoundError,
    ProjectCreationError,
    ValidationError
)


def create_project_membership(
    project_details: ProjectCreateSchema,
    user_id: UUID,
    db: Session,
) -> ProjectResponseSchema:
    """
    Create a new project with owner membership.
    
    Business Rules:
    - Max 20 projects per user
    - Creator is automatically OWNER
    """
    user_projects_count = (
        db.query(Project)
        .join(Membership)
        .filter(Membership.user_id == user_id)
        .count()
    )

    if user_projects_count >= 20:
        logger.warning(
            "Project creation blocked - max projects reached",
            extra={"user_id": str(user_id), "projects_count": user_projects_count}
        )

        raise ValidationError("You have reached the maximum of 20 projects")
    
    try:
        new_project = Project(
            name=project_details.name,
            owner_id=user_id,
        )
        db.add(new_project)
        db.flush()

        new_membership = Membership(
            user_id=user_id,
            project_id=new_project.id,
            role=UserRole.OWNER,
        )
        db.add(new_membership)
        db.commit()
        db.refresh(new_project)
        
        logger.info(
            "Project created with owner membership",
            extra={
                "project_id": str(new_project.id),
                "project_name": new_project.name,
                "owner_id": str(user_id)
            }
        )

        return new_project
        
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise ProjectCreationError("Failed to create project") from e


def get_projects(
    user_id: UUID,
    pagination: "PaginationParams",
    sort_params: "SortParams",
    name_filter: str | None,
    db: Session
) -> "PaginatedResponse[Project]":
    """
    Get paginated, sorted, and filtered projects where user is a member.
    
    Filters:
    - name_filter: Search by project name (case-insensitive)
    
    Sortable fields: name, created_at
    """
    #avoid N+1 by eager loading memberships and filtering in Python
    query = (
        db.query(Project)
        .options(selectinload(Project.memberships))  
        .join(Membership)
        .filter(Membership.user_id == user_id)
    )
    
    # Apply filters
    if name_filter:
        query = query.filter(Project.name.ilike(f"%{name_filter}%"))
    
    # Apply sorting
    allowed_sort_fields = ["name", "created_at"]
    query = apply_sorting(query, sort_params, Project, allowed_sort_fields)
    
    # Apply pagination
    return paginate(query, pagination, Project)


def get_project_by_id(project_id: UUID, db: Session) -> Project:
    """Get project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")
    return project


def update_project(
    project_id: UUID,
    project_data: ProjectUpdateSchema,
    db: Session
) -> Project:
    """Update project name."""
    project = get_project_by_id(project_id, db)
    
    project.name = project_data.name
    db.commit()
    db.refresh(project)
    
    logger.info(
        "Project updated",
        extra={
            "project_id": str(project_id),
            "new_name": project_data.name
        }
    )

    return project


def delete_project(project_id: UUID, db: Session) -> None:
    """Delete project (hard delete with cascade)."""
    project = get_project_by_id(project_id, db)
    
    try:
        db.delete(project)
        db.commit()
        logger.info(
            "Project deleted",
            extra={"project_id": str(project_id), "project_name": project.name}
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting project: {str(e)}", exc_info=True)
        raise


def get_project_members(project_id: UUID, db: Session) -> list[Membership]:
    """Get all members of a project."""
    return (
        db.query(Membership)
        .filter(Membership.project_id == project_id)
        .all()
    )