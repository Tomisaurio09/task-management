# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_token
from uuid import UUID
from app.models.membership import Membership, UserRole
from app.core.exceptions import InsufficientPermissionsError, ResourceNotFoundError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> dict:
    payload = verify_token(token, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
            )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = UUID(sub)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user.id, "instance": user}


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
        if not membership:
            raise ResourceNotFoundError("You are not a member of this project")
        if membership.role not in allowed_roles:
            raise InsufficientPermissionsError(f"You need one of these roles: {[r.value for r in allowed_roles]}")
        return membership
    return dependency
