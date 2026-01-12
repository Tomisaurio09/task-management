from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from ..db.dependencies import get_db
from ..models.project import Project
from ..models.membership import Membership
from sqlalchemy.orm import Session
from ..auth.oauth2 import get_current_user
from ..auth.roles import require_owner, require_editor, require_viewer
from typing import Annotated
from fastapi import Depends, Path
router = APIRouter(tags=["projects"])
#MANEJAR ROLES A FUTURO
#CUANDO SE CREA UN PROYECTO, SE DEBE CREAR UNA MEMBERSHIP AUTOMATICAMENTE PARA EL OWNER
#ALGUN ENDPOINT QUE PERMITA AGREGAR MIEMBROS A UN PROYECTO, CON SU RESPECTIVO ROL

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponseSchema)
def create_project(current_user=Depends(get_current_user),project_details: ProjectCreateSchema = Body(...),db: Session = Depends(get_db)):
    new_project = Project(
        name=project_details.name,
        owner_id=current_user.get("id")
    )
    db.add(new_project)
    db.flush()  # adds new project but it doesnt close the transaction yet

    new_membership = Membership(
        user_id=current_user.get("id"),
        project_id=new_project.id,
        role="OWNER"
    )
    db.add(new_membership)

    db.commit()          # save both project and membership
    db.refresh(new_project)
    return new_project


@router.get("/", response_model=list[ProjectResponseSchema])
def get_projects(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """It is normal for the user to see all the projects where he is owner, editor or viewer"""
    projects = (
    db.query(Project)
    .join(Membership)
    .filter(Membership.user_id == current_user["id"])
    .all()
    )
    return projects

@router.get("/{project_id}", response_model=ProjectResponseSchema)
def get_project(project_id: UUID, current_user=Depends(require_viewer), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponseSchema)
def update_project(project_id: UUID, project_details: ProjectUpdateSchema, current_user=Depends(require_editor), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.name = project_details.name
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, current_user=Depends(require_owner), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}