# app/api/tasks.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema, TaskResponseSchema
from app.core.dependencies import get_db, require_project_roles
from app.models.membership import UserRole
from app.services import task_service

router = APIRouter(tags=["tasks"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponseSchema)
def create_task(
    project_id: UUID,
    board_id: UUID,
    task_data: TaskCreateSchema = Body(...),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Create a new task in the board."""
    return task_service.create_task(project_id, board_id, task_data, db)


@router.get("/", response_model=list[TaskResponseSchema])
def get_tasks(
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """List all active tasks in the board."""
    return task_service.get_tasks(board_id, include_archived=False, db=db)


@router.get("/archived", response_model=list[TaskResponseSchema])
def get_archived_tasks(
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """List all archived tasks in the board."""
    return task_service.get_tasks(board_id, include_archived=True, db=db)


@router.get("/{task_id}", response_model=TaskResponseSchema)
def get_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """Get a specific task."""
    return task_service.get_task_by_id(board_id, task_id, db)


@router.patch("/{task_id}", response_model=TaskResponseSchema)
def update_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    task_data: TaskUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """
    Update a task.
    
    Note: Changing board_id will move the task to another board
    (must be in the same project).
    """
    return task_service.update_task(project_id, board_id, task_id, task_data, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Delete a task."""
    task_service.delete_task(board_id, task_id, db)