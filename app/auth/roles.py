# app/auth/roles.py
from fastapi import HTTPException
from app.models.membership import Membership, UserRole
from sqlalchemy.orm import Session
from uuid import UUID

def check_project_role(
    project_id: UUID,
    user_id: UUID,
    allowed_roles: list[UserRole],  
    db: Session
):
    """Verifies if the user has one of the allowed roles in the specified project."""
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user_id, Membership.project_id == project_id)
        .first()
    )
    
    if not membership or membership.role not in allowed_roles:
        raise HTTPException(
            status_code=403, 
            detail="You do not have the required permissions to access this resource."
        )
    return membership