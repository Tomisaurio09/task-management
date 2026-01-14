# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from ..db.dependencies import get_db
from ..models.project import Project
from ..models.membership import Membership, UserRole  
from sqlalchemy.orm import Session
from ..auth.oauth2 import get_current_user
from ..auth.roles import check_project_role
from ..services import memberships
from ..schemas.membership_schema import AddMemberSchema, ChangeRoleMemberSchema, MemberResponseSchema
router = APIRouter(tags=["projects"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponseSchema)
def create_project(
    project_details: ProjectCreateSchema = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_project = Project(
        name=project_details.name,
        owner_id=current_user["id"]
    )
    db.add(new_project)
    db.flush()

    new_membership = Membership(
        user_id=current_user["id"],
        project_id=new_project.id,
        role=UserRole.OWNER
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.get("/", response_model=list[ProjectResponseSchema])
def get_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = (
        db.query(Project)
        .join(Membership)
        .filter(Membership.user_id == current_user["id"])
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponseSchema)
def get_project(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],  
        db=db
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponseSchema)
def update_project(
    project_id: UUID,
    project_details: ProjectUpdateSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],  
        db=db
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.name = project_details.name
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER],  
        db=db
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None

#business logic
@router.get("/{project_id}/members", response_model=list[MemberResponseSchema])
def list_members_endpoint(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    members = (
        db.query(Membership)
        .filter(Membership.project_id == project_id)
        .all()
    )
    return members

@router.post("/{project_id}/members/add/{user_id}", status_code=status.HTTP_201_CREATED)
def add_member_endpoint(project_id: UUID, user_id: UUID, body: AddMemberSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER],  
        db=db
    )
    return memberships.add_member(project_id, user_id, body.role, current_user["id"], db)


@router.delete("/{project_id}/members/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_endpoint(project_id: UUID, user_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER],  
        db=db
    )
    return memberships.remove_member(project_id, user_id, db)

@router.patch("/{project_id}/members/change-role/{user_id}", status_code=status.HTTP_200_OK)
def change_member_role_endpoint(project_id: UUID, user_id: UUID, body: ChangeRoleMemberSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER],  
        db=db
    )
    return memberships.change_member_role(project_id, user_id, body.role, db)