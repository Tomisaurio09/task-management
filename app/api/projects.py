# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from app.schemas.membership_schema import AddMemberSchema, ChangeRoleMemberSchema, MemberResponseSchema
from app.core.dependencies import get_db, get_current_user, require_project_roles
from app.models.membership import UserRole
from app.services import project_service, membership_service


router = APIRouter(tags=["projects"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponseSchema)
def create_project(
    project_details: ProjectCreateSchema = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return project_service.create_project_membership(
        project_details=project_details,
        user_id=current_user["id"],
        db=db,
    )


@router.get("/", response_model=list[ProjectResponseSchema])
def get_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return project_service.get_projects(current_user["id"], db)


@router.get("/{project_id}", response_model=ProjectResponseSchema)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    return project_service.get_project_by_id(project_id, db)



@router.patch("/{project_id}", response_model=ProjectResponseSchema)
def update_project(
    project_id: UUID,
    project_data: ProjectUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))

):
    return project_service.update_project(project_id, project_data, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    project_service.delete_project(project_id, db)

#Membership endpoints

@router.get("/{project_id}/members", response_model=list[MemberResponseSchema])
def list_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    return project_service.get_project_members(project_id, db)


@router.post("/{project_id}/members/add/{user_id}", status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: UUID,
    user_id: UUID,
    body: AddMemberSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    return membership_service.add_member(
        project_id, user_id, body.role, current_user["id"], db
    )


@router.delete("/{project_id}/members/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_endpoint(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
    ):

    membership_service.remove_member(project_id, user_id, db)

@router.patch("/{project_id}/members/change-role/{user_id}", status_code=status.HTTP_200_OK)
def change_member_role_endpoint(
    project_id: UUID,
    user_id: UUID,
    body: ChangeRoleMemberSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
    ):

    return membership_service.change_member_role(project_id, user_id, body.role, db)
