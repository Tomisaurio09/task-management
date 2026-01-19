# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.db.session import SessionLocal
from app.models.user import User
from security import verify_token
from uuid import UUID
from app.models.membership import Membership, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth dependency
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> dict:
    payload = verify_token(token, "access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user.id, "instance": user}


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
