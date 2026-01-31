# app/services/task_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.membership import Membership
from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from app.schemas.pagination import PaginationParams, SortParams, PaginatedResponse
from app.core.pagination import apply_sorting, paginate
from app.models.task import TaskStatus, PriorityLevel
from app.core.logger import logger
from app.core.exceptions import (
    TaskNotFoundError,
    TaskCreationError,
    InvalidAssigneeError,
    ValidationError,
)


def _validate_assignee(assignee_id: UUID, project_id: UUID, db: Session) -> None:
    """Validate that assignee is a project member."""
    if assignee_id:
        assignee_membership = db.query(Membership).filter(
            Membership.user_id == assignee_id,
            Membership.project_id == project_id
        ).first()
        
        if not assignee_membership:
            raise InvalidAssigneeError("Assignee must be a project member")


def create_task(
    project_id: UUID,
    board_id: UUID,
    task_data: TaskCreateSchema,
    db: Session
) -> Task:
    """Create a new task in a board."""
    # Validate assignee if provided
    if task_data.assignee_id:
        _validate_assignee(task_data.assignee_id, project_id, db)
    
    try:
        # Get max position for this board
        max_position_task = db.query(Task).filter(
            Task.board_id == board_id
        ).order_by(Task.position.desc()).first()
        
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

#the only modified function
def get_tasks(
    board_id: UUID,
    include_archived: bool,
    pagination: "PaginationParams",
    sort_params: "SortParams",
    status_filter: "TaskStatus | None",
    priority_filter: "PriorityLevel | None",
    assignee_filter: UUID | None,
    db: Session
) -> "PaginatedResponse[Task]":
    """
    Get paginated, sorted, and filtered tasks for a board.
    
    Filters:
    - include_archived: Include archived tasks
    - status_filter: Filter by task status (ACTIVE, COMPLETED, ARCHIVED)
    - priority_filter: Filter by priority (LOW, MEDIUM, HIGH)
    - assignee_filter: Filter by assignee user ID
    
    Sortable fields: name, position, created_at, updated_at, due_date, status, priority
    """
    
    query = db.query(Task).filter(Task.board_id == board_id)
    
    # Filter archived
    if not include_archived:
        query = query.filter(Task.archived == False)
    
    # Filter by status
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    # Filter by priority
    if priority_filter:
        query = query.filter(Task.priority == priority_filter)
    
    # Filter by assignee
    if assignee_filter:
        query = query.filter(Task.assignee_id == assignee_filter)
    
    # Apply sorting
    allowed_sort_fields = ["name", "position", "created_at", "updated_at", "due_date", "status", "priority"]
    query = apply_sorting(query, sort_params, Task, allowed_sort_fields)
    
    # If no sorting specified, default to position
    if not sort_params.sort_by:
        query = query.order_by(Task.position.asc())
    
    # Apply pagination
    return paginate(query, pagination, Task)


def get_task_by_id(board_id: UUID, task_id: UUID, db: Session) -> Task:
    """Get a specific task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.board_id == board_id
    ).first()
    
    if not task:
        raise TaskNotFoundError(f"Task {task_id} not found in board {board_id}")
    
    return task


def update_task(
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    task_data: TaskUpdateSchema,
    db: Session
) -> Task:
    """Update a task."""
    task = get_task_by_id(board_id, task_id, db)
    
    # Validate assignee if being changed
    if task_data.assignee_id is not None:
        _validate_assignee(task_data.assignee_id, project_id, db)
    
    # Validate board_id change (must stay in same project)
    if task_data.board_id and task_data.board_id != board_id:
        # For now, we'll allow it since the endpoint enforces project_id
        pass
    
    # Update allowed fields
    ALLOWED_FIELDS = {
        "name", "position", "archived", "status", "priority",
        "assignee_id", "description", "due_date", "board_id"
    }
    
    update_data = task_data.model_dump(exclude_unset=True)
    if "assignee_id" in update_data and update_data["assignee_id"] is None:
        task.assignee_id = None

    
    for field, value in update_data.items():
        if field in ALLOWED_FIELDS:
            setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task {task_id} updated")
    return task


def delete_task(board_id: UUID, task_id: UUID, db: Session) -> None:
    """Delete a task (hard delete)."""
    task = get_task_by_id(board_id, task_id, db)
    
    try:
        db.delete(task)
        db.commit()
        logger.info(f"Task {task_id} deleted from board {board_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting task: {str(e)}", exc_info=True)
        raise