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

def add_member(project_id: UUID, user_id: UUID, role: UserRole, current_user_id: UUID, db: Session):
    existing = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="The user is already a member of the project")

    new_member = Membership(user_id=user_id, project_id=project_id, role=role, invited_by=current_user_id)
    db.add(new_member)
    db.commit()
    return new_member

def remove_member(project_id: UUID, user_id: UUID, db: Session):
    member = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in the project")

    if member.role == UserRole.OWNER:
        owners_count = db.query(Membership).filter_by( project_id=project_id, role=UserRole.OWNER ).count()
        if owners_count <= 1:
            raise HTTPException(status_code=400, detail="The project must have at least one OWNER")

    db.delete(member)
    db.commit()
    return {"message": "Member removed successfully"}

def change_member_role(project_id: UUID, user_id: UUID, new_role: UserRole, db: Session):
    member = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in the project")

    if member.role == new_role:
        raise HTTPException(status_code=400, detail="The member already has this role")
    
    member.role = new_role
    db.commit()
    return member

