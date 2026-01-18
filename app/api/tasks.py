# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.task_schema import TaskCreateSchema, TaskUpdateSchema, TaskResponseSchema
from ..db.dependencies import get_db
from ..models.task import Task
from ..models.membership import UserRole, Membership
from sqlalchemy.orm import Session
from ..auth.oauth2 import get_current_user
from ..auth.roles import check_project_role

router = APIRouter(tags=["tasks"] )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponseSchema)
def create_task(
    project_id: UUID,
    board_id: UUID,
    task_details:TaskCreateSchema = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],
        db=db
    )
    max_position = (
        db.query(Task)
        .filter(Task.board_id == board_id)
        .order_by(Task.position.desc())
        .first()
    )
    next_position = (max_position.position + 1) if max_position else 0

    if task_details.assignee_id:
        assignee_membership = db.query(Membership).filter(
            Membership.user_id == task_details.assignee_id,
            Membership.project_id == project_id
        ).first()
    if not assignee_membership:
        raise HTTPException(status_code=400, detail="Assignee must be a project member")
    
    new_task = Task(
        **task_details.model_dump(exclude={"board_id", "position"}),
        board_id=board_id,
        position=next_position
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/", response_model=list[TaskResponseSchema])
def get_tasks(
    project_id: UUID,
    board_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    tasks = (
        db.query(Task)
        .filter(Task.board_id == board_id, Task.archived == False)
        .order_by(Task.position.asc())
        .all()
    )
    return tasks

@router.get("/archived", response_model=list[TaskResponseSchema])
def get_archived_tasks(
    project_id: UUID,
    board_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    tasks = (
        db.query(Task)
        .filter(Task.board_id == board_id, Task.archived == True)
        .order_by(Task.position.asc())
        .all()
    )
    return tasks

@router.get("/{task_id}", response_model=TaskResponseSchema)
def get_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.board_id == board_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

@router.patch("/{task_id}", response_model=TaskResponseSchema)
def update_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    task_details: TaskUpdateSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Changing the board_id of a task will move the task to another board."""
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],
        db=db
    )

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.board_id == board_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    ALLOWED_FIELDS = {
    "name",
    "position",
    "archived",
    "status",
    "priority",
    "assignee_id",
    "description",
    "due_date",
    "board_id"
    }
    if task_details.assignee_id:
        assignee_membership = db.query(Membership).filter(
            Membership.user_id == task_details.assignee_id,
            Membership.project_id == project_id
        ).first()
    if not assignee_membership:
        raise HTTPException(status_code=400, detail="Assignee must be a project member")
    
    if task_details.board_id != board_id:
        raise HTTPException(status_code=400, detail="Task can only move to another board if this board is in the same project.")

    update_data = task_details.model_dump(exclude_none=True)

    for field, value in update_data.items():
        if field in ALLOWED_FIELDS:
            setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],
        db=db
    )

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.board_id == board_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    db.delete(task)
    db.commit()
    return None