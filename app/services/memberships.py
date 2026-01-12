# app/services/memberships.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.membership import Membership, UserRole


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

