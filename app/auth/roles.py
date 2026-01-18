# app/auth/roles.py
from fastapi import HTTPException, Depends
from app.auth.oauth2 import get_current_user
from app.models.membership import Membership, UserRole
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.dependencies import get_db

#FUNCIONA COMO DEPENDENCIA
def require_project_roles(
    allowed_roles: list[UserRole],
):
    def dependency(
        project_id: UUID,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == current_user["id"],
                Membership.project_id == project_id,
            )
            .first()
        )

        if not membership or membership.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have the required permissions to access this resource.",
            )

        return membership

    return dependency
