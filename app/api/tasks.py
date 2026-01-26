# app/api/tasks.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body, Query, Request
from sqlalchemy.orm import Session

from app.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema, TaskResponseSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse, SortParams
from app.core.dependencies import get_db, require_project_roles
from app.core.rate_limit import limiter
from app.models.membership import UserRole
from app.models.task import TaskStatus, PriorityLevel
from app.services import task_service

router = APIRouter(tags=["tasks"])


#El que mas cambia es el get all tasks, los demas solo se les agrega un limiter
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponseSchema)
@limiter.limit("50/minute")
def create_task(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    task_data: TaskCreateSchema = Body(...),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Create a new task in the board."""
    return task_service.create_task(project_id, board_id, task_data, db)


@router.get("/", response_model=PaginatedResponse[TaskResponseSchema])
@limiter.limit("120/minute")
def get_tasks(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER])),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    # Sorting
    sort_by: str | None = Query(
        None, 
        description="Sort by: name, position, created_at, updated_at, due_date, status, priority"
    ),
    sort_order: str = Query("asc", description="asc or desc"),
    # Filters
    archived: bool = Query(False, description="Include archived tasks"),
    status: TaskStatus | None = Query(None, description="Filter by status"),
    priority: PriorityLevel | None = Query(None, description="Filter by priority"),
    assignee_id: UUID | None = Query(None, description="Filter by assignee")
):
    """
    List tasks (paginated, sortable, filterable).
    
    **Filters:**
    - archived: Include archived tasks
    - status: ACTIVE, COMPLETED, ARCHIVED
    - priority: LOW, MEDIUM, HIGH
    - assignee_id: UUID of assigned user
    
    **Sort by:** name, position, created_at, updated_at, due_date, status, priority
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    sort_params = SortParams(sort_by=sort_by, sort_order=sort_order)
    
    return task_service.get_tasks(
        board_id=board_id,
        include_archived=archived,
        pagination=pagination,
        sort_params=sort_params,
        status_filter=status,
        priority_filter=priority,
        assignee_filter=assignee_id,
        db=db
    )


@router.get("/{task_id}", response_model=TaskResponseSchema)
@limiter.limit("150/minute")
def get_task(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """Get a specific task."""
    return task_service.get_task_by_id(board_id, task_id, db)


@router.patch("/{task_id}", response_model=TaskResponseSchema)
@limiter.limit("100/minute")
def update_task(
    request: Request,
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
@limiter.limit("30/minute")
def delete_task(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Delete a task."""
    task_service.delete_task(board_id, task_id, db)