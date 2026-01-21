# app/api/boards.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.schemas.board_schema import BoardCreateSchema, BoardUpdateSchema, BoardResponseSchema
from app.core.dependencies import get_db, require_project_roles
from app.models.membership import UserRole
from app.services import board_service

router = APIRouter(tags=["boards"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BoardResponseSchema)
def create_board(
    project_id: UUID,
    board_data: BoardCreateSchema = Body(...),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Create a new board in the project."""
    return board_service.create_board(project_id, board_data, db)


@router.get("/", response_model=list[BoardResponseSchema])
def get_boards(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """List all active boards in the project."""
    return board_service.get_boards(project_id, include_archived=False, db=db)


@router.get("/archived", response_model=list[BoardResponseSchema])
def get_archived_boards(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """List all archived boards in the project."""
    return board_service.get_boards(project_id, include_archived=True, db=db)


@router.get("/{board_id}", response_model=BoardResponseSchema)
def get_board(
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """Get a specific board."""
    return board_service.get_board_by_id(project_id, board_id, db)


@router.patch("/{board_id}", response_model=BoardResponseSchema)
def update_board(
    project_id: UUID,
    board_id: UUID,
    board_data: BoardUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Update a board."""
    return board_service.update_board(project_id, board_id, board_data, db)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    project_id: UUID,
    board_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Delete a board and all its tasks."""
    board_service.delete_board(project_id, board_id, db)