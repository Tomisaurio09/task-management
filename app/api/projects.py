# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from ..core.dependencies import get_db, get_current_user, require_project_roles
from ..models.project import Project
from ..models.membership import Membership, UserRole  
from sqlalchemy.orm import Session
from ..services import projects_services
from ..schemas.membership_schema import AddMemberSchema, ChangeRoleMemberSchema, MemberResponseSchema
router = APIRouter(tags=["projects"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponseSchema)
def create_project(
    project_details: ProjectCreateSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return projects_services.create_project_membership(
        project_details=project_details,
        user_id=current_user["id"],
        db=db,
    )


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
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponseSchema)
def update_project(
    project_id: UUID,
    project_details: ProjectUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):

    
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
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    
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
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):


    members = (
        db.query(Membership)
        .filter(Membership.project_id == project_id)
        .all()
    )
    return members

@router.post("/{project_id}/members/add/{user_id}", status_code=status.HTTP_201_CREATED)
def add_member_endpoint(
    project_id: UUID,
    user_id: UUID,
    body: AddMemberSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
    ):

    return projects_services.add_member(project_id, user_id, body.role, current_user["id"], db)


@router.delete("/{project_id}/members/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_endpoint(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
    ):

    return projects_services.remove_member(project_id, user_id, db)

@router.patch("/{project_id}/members/change-role/{user_id}", status_code=status.HTTP_200_OK)
def change_member_role_endpoint(
    project_id: UUID,
    user_id: UUID,
    body: ChangeRoleMemberSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
    ):

    return projects_services.change_member_role(project_id, user_id, body.role, db)