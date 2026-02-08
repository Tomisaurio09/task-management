# app/api/boards.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body, Query, Request
from sqlalchemy.orm import Session

from app.schemas.board_schema import BoardCreateSchema, BoardUpdateSchema, BoardResponseSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse, SortParams
from app.core.dependencies import get_db, require_project_roles
from app.core.rate_limit import limiter
from app.models.membership import UserRole
from app.services import board_service

router = APIRouter(tags=["boards"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BoardResponseSchema)
@limiter.limit("20/minute")
def create_board(
    request: Request,
    project_id: UUID,
    board_data: BoardCreateSchema = Body(...),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Create a new board in the project."""
    return board_service.create_board(project_id, board_data, db)


@router.get("/", response_model=PaginatedResponse[BoardResponseSchema])
@limiter.limit("100/minute")
def get_boards(
    request: Request,
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER])),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    # Sorting
    sort_by: str | None = Query(None, description="Sort by: name, position, created_at, updated_at"),
    sort_order: str = Query("asc", description="asc or desc"),
    # Filters
    name: str | None = Query(None, description="Filter by name"),
    archived: bool = Query(False, description="Include archived boards")
):
    """List boards (paginated, sortable, filterable)."""
    pagination = PaginationParams(page=page, page_size=page_size)
    sort_params = SortParams(sort_by=sort_by, sort_order=sort_order)
    
    return board_service.get_boards(
        project_id=project_id,
        include_archived=archived,
        pagination=pagination,
        sort_params=sort_params,
        name_filter=name,
        db=db
    )


@router.get("/{board_id}", response_model=BoardResponseSchema)
@limiter.limit("120/minute")
def get_board(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """Get a specific board."""
    return board_service.get_board_by_id(project_id, board_id, db)


@router.patch("/{board_id}", response_model=BoardResponseSchema)
@limiter.limit("60/minute")
def update_board(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    board_data: BoardUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Update a board."""
    return board_service.update_board(project_id, board_id, board_data, db)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def delete_board(
    request: Request,
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Delete a board and all its tasks."""
    board_service.delete_board(project_id, board_id, db)