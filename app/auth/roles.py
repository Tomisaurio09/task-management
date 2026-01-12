from fastapi import Depends, HTTPException
from app.auth.oauth2 import get_current_user
from app.db.dependencies import get_db
from app.models.membership import Membership
from sqlalchemy.orm import Session
from uuid import UUID

def require_owner(project_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(Membership).filter_by(
        user_id=current_user.get("id"),
        project_id=project_id
    ).first()
    if not membership or membership.role != "OWNER":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def require_editor(project_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(Membership).filter_by(
        user_id=current_user.get("id"),
        project_id=project_id
    ).first()
    if not membership or membership.role not in ["OWNER", "EDITOR"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def require_viewer(project_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(Membership).filter_by(
        user_id=current_user.get("id"),
        project_id=project_id
    ).first()
    if not membership or membership.role not in ["OWNER", "EDITOR", "VIEWER"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

