# app/services/memberships.pyfrom uuid import UUID
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.membership import Membership, UserRole
from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema
from app.core.logger import logger
from app.core.exceptions import (
    ProjectNotFoundError,
    ProjectCreationError,
    ValidationError
)
#POST, GET, GET, PATCH, DELETE
#LOS SERVICIOS NO TIENEN QUE USAR DEPENDS NI BODY NI HTTPEXCEPTION
def create_project_membership(
    project_details: ProjectCreateSchema,
    owner_id: UUID,
    db: Session,
)-> Project:
    user_projects_counts = (
        db.query(Project)
        .join(Membership)
        .filter(Membership.user_id == owner_id)
        .count()
    )

    if user_projects_counts >= 20:
        raise ValidationError("User has reached the maximum number of projects allowed.")
    try:
        new_project = Project(
            name=project_details.name,
            owner_id=owner_id,
        )
        db.add(new_project)
        db.flush()

        new_membership = Membership(
            user_id=owner_id,
            project_id=new_project.id,
            role=UserRole.OWNER,
        )
        db.add(new_membership)
        db.commit()
        db.refresh(new_project)
        logger.info(f"Project created: {new_project.name} by User ID: {owner_id}")
        return new_project
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise ProjectCreationError("Failed to create project") from e
    
def get_projects(user_id: UUID, db: Session) -> list[Project]:
    return (
        db.query(Project)
        .join(Membership)
        .filter(Membership.user_id==user_id)
        .all()
    )

def get_project_by_id(db:Session, project_id:UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")
    return project

def update_project(db:Session, project_id:UUID, project_details: ProjectUpdateSchema) -> Project:
    project = get_project_by_id(db,project_id)
    
    project.name = project_details.name
    db.commit()
    db.refresh(project)
    logger.info(f"Project {project_id} updated")
    return project

def delete_project(db:Session, project_id:UUID)->None:
    project = get_project_by_id(db,project_id)
    try:
        db.delete(project)
        db.commit()
        logger.info(f"Project {project_id} deleted")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting project: {str(e)}", exc_info=True)
        raise

def get_project_members(db:Session, project_id:UUID) -> list[Membership]:
    return(
        db.query(Membership)
        .filter(Membership.project_id == project_id)
        .all()
    )