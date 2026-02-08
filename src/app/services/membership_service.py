from uuid import UUID
from sqlalchemy.orm import Session
from app.models.membership import Membership, UserRole
from app.schemas.membership_schema import MemberResponseSchema
from app.core.logger import logger
from app.core.exceptions import (
    MemberAlreadyExistsError,
    LastOwnerError,
    ResourceNotFoundError,
    ValidationError
)

def add_member(project_id: UUID, user_id: UUID, role: UserRole, invited_by: UUID, db: Session) -> MemberResponseSchema:
    existing = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if existing:
        logger.warning(
            "Attempt to add existing member",
            extra={"project_id": str(project_id), "user_id": str(user_id)}
        )

        raise MemberAlreadyExistsError("User is already a member of this project")

    try:
        new_member = Membership(user_id=user_id, project_id=project_id, role=role, invited_by=invited_by)
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        logger.info(
            "Member added to project",
            extra={
                "project_id": str(project_id),
                "user_id": str(user_id),
                "role": role.value,
                "invited_by": str(invited_by)
            }
        )

        return new_member

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding member: {str(e)}", exc_info=True)
        raise

def remove_member(project_id: UUID, user_id: UUID, db: Session) -> None:
    member = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if not member:
        raise ResourceNotFoundError("Member not found in project")

    if member.role == UserRole.OWNER:
        owners_count = db.query(Membership).filter_by( project_id=project_id, role=UserRole.OWNER ).count()
        if owners_count <= 1:
            logger.warning(
                "Attempt to remove last owner",
                extra={"project_id": str(project_id), "user_id": str(user_id)}
            )

            raise LastOwnerError("Cannot remove the last owner of the project")

    try:
        db.delete(member)
        db.commit()
        logger.info(
            "Member removed from project",
            extra={
                "project_id": str(project_id),
                "user_id": str(user_id),
                "role": member.role.value
            }
        )

    except LastOwnerError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing member: {str(e)}", exc_info=True)
        raise

def change_member_role(project_id: UUID, user_id: UUID, new_role: UserRole, db: Session) -> Membership:
    member = db.query(Membership).filter_by(user_id=user_id, project_id=project_id).first()
    if not member:
        raise ResourceNotFoundError("Member not found in the project")

    if member.role == new_role:
        logger.warning(
            "Attempt to change role to same value",
            extra={
                "project_id": str(project_id),
                "user_id": str(user_id),
                "role": new_role.value
            }
        )

        raise ValidationError(f"Member already has role {new_role.value}")
    
    try:
        member.role = new_role
        db.commit()
        db.refresh(member)
        
        logger.info(
            "Member role changed",
            extra={
                "project_id": str(project_id),
                "user_id": str(user_id),
                "old_role": member.role.value,
                "new_role": new_role.value
            }
        )

        return member
    
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing member role: {str(e)}", exc_info=True)
        raise

