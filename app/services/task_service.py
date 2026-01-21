from uuid import UUID
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema, TaskResponseSchema
from app.models.membership import Membership
from app.core.logger import logger
from app.core.exceptions import (
    TaskNotFoundError,
    TaskCreationError,
    InvalidAssigneeError,
    ValidationError
)

def _validate_assignee(assigne_id:UUID, project_id:UUID, db:Session) -> None:
    if assigne_id:
        assigne_membership = db.query(Membership).filter(
            Membership.user_id == assigne_id,
            Membership.project_id == project_id
        ).first()

        if not assigne_membership:
            raise InvalidAssigneeError("Assigne must be a project member")
        
def create_task(
        project_id:UUID,
        board_id:UUID,
        task_data:TaskCreateSchema,
        db: Session
) -> Task:
    if task_data.assignee_id:
        _validate_assignee(task_data.assignee_id, project_id, db)

    try:
        max_position_task = db.query(Task).filter(
            Task.board_id == board_id
        ).order_by(Task.position.desc()).first

        next_position = (max_position_task.position + 1) if max_position_task else 0

        new_task = Task(
            **task_data.model_dump(exclude={"board_id", "position"}),
            board_id=board_id,
            position=next_position
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        logger.info(f"Task '{new_task.name}' created in board {board_id}")
        return new_task
    except InvalidAssigneeError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        raise TaskCreationError("Failed to create task") from e
    
def get_tasks(board_id:UUID, include_archived:bool, db:Session) -> list[TaskResponseSchema]:
    query = (
        db.query(Task)
        .filter(Task.board_id == board_id)
    )
    if not include_archived:
        query=query.filter(Task.archived==False)
    return query.order_by(Task.position.asc()).all()

def get_task_by_id(
    board_id: UUID,
    task_id: UUID,
    db: Session
)-> TaskResponseSchema:

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.board_id == board_id)
        .first()
    )
    if not task:
        raise TaskNotFoundError(f"Task {task_id} not found in board {board_id}")
    return task

def update_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    task_data: TaskUpdateSchema,
    db: Session
)-> TaskResponseSchema:
    task = get_task_by_id(board_id, task_id, db)

    if task_data.assignee_id is not None:
        _validate_assignee(task_data.assignee_id, project_id, db)
    
    if task_data.board_id != board_id:
        raise ValidationError("Task can only move to another board if this board is in the same project.")
    
    ALLOWED_FIELDS = {
        "name", "position", "archived", "status", "priority",
        "assignee_id", "description", "due_date", "board_id"
    }

    update_data = task_data.model_dump(exclude_none=True)

    for field, value in update_data.items():
        if field in ALLOWED_FIELDS:
            setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} updated")
    return task

def delete_task(
    board_id: UUID,
    task_id: UUID,
    db: Session
)-> None:
    try:
        task = get_task_by_id(board_id, task_id, db)

        db.delete(task)
        db.commit()
        logger.info(f"Task {task_id} deleted from board {board_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting task: {str(e)}", exc_info=True)
        raise
