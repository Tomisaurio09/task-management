from uuid import UUID
from sqlalchemy.orm import Session
from app.models.board import Board
from app.schemas.board_schema import BoardCreateSchema, BoardUpdateSchema, BoardResponseSchema
from app.core.logger import logger
from app.core.exceptions import (
    BoardNotFoundError,
    BoardCreationError,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, SortParams
from app.core.pagination import apply_sorting, paginate

def create_board(
    project_id: UUID,
    board_data: BoardCreateSchema,
    db: Session
) -> Board:
    """Create a new board in a project."""
    #It doesnt check if the project already exist but it tells the user that they are not a member of the project, so an error is thrown
    try:
        # Get max position for this project
        max_position_row = db.query(Board).filter(
            Board.project_id == project_id
        ).order_by(Board.position.desc()).first()
        
        next_position = (max_position_row.position + 1) if max_position_row else 0
        
        new_board = Board(
            name=board_data.name,
            project_id=project_id,
            position=next_position
        )
        db.add(new_board)
        db.commit()
        db.refresh(new_board)
        
        logger.info(
            f"Board created",
            extra={
                "board_id": str(new_board.id),
                "board_name": new_board.name,
                "project_id": str(project_id)
            }
        )

        return new_board
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating board: {str(e)}", exc_info=True)
        raise BoardCreationError("Failed to create board") from e


def get_boards(
    project_id: UUID,
    include_archived: bool,
    pagination: "PaginationParams",
    sort_params: "SortParams",
    name_filter: str | None,
    db: Session
) -> "PaginatedResponse[BoardResponseSchema]":
    """
    Get paginated, sorted, and filtered boards for a project.
    
    Filters:
    - include_archived: Include archived boards
    - name_filter: Search by board name (case-insensitive)
    
    Sortable fields: name, position, created_at, updated_at
    """
    
    query = db.query(Board).filter(Board.project_id == project_id)
    
    # Filter archived
    if not include_archived:
        query = query.filter(Board.archived == False)
    
    # Filter by name
    if name_filter:
        query = query.filter(Board.name.ilike(f"%{name_filter}%"))
    
    # Apply sorting
    allowed_sort_fields = ["name", "position", "created_at", "updated_at"]
    query = apply_sorting(query, sort_params, Board, allowed_sort_fields)
    
    # If no sorting specified, default to position
    if not sort_params.sort_by:
        query = query.order_by(Board.position.asc())
    
    # Apply pagination
    return paginate(query, pagination, Board)


def get_board_by_id(project_id: UUID, board_id: UUID, db: Session) -> Board:
    """Get a specific board."""
    board = db.query(Board).filter(
        Board.id == board_id,
        Board.project_id == project_id
    ).first()
    
    if not board:
        raise BoardNotFoundError(f"Board {board_id} not found in project {project_id}")
    
    return board


def update_board(
    project_id: UUID,
    board_id: UUID,
    board_data: BoardUpdateSchema,
    db: Session
) -> Board:
    """Update a board."""
    board = get_board_by_id(project_id, board_id, db)
    old_name = board.name
    
    # Update only provided fields
    if board_data.name is not None:
        board.name = board_data.name
    if board_data.position is not None:
        board.position = board_data.position
    if board_data.archived is not None:
        board.archived = board_data.archived
    
    db.commit()
    db.refresh(board)

    logger.info(
        f"Board updated",
        extra={
            "board_id": str(board_id),
            "old_name": old_name,
            "new_name": board.name,
            "board_name": str(board.name),
            "project_id": str(project_id),
        }
    )

    return board


def delete_board(project_id: UUID, board_id: UUID, db: Session) -> None:
    """Delete a board (hard delete)."""
    board = get_board_by_id(project_id, board_id, db)
    board_name = board.name
    try:
        db.delete(board)
        db.commit()

        logger.info(
            f"Board deleted",
            extra={
                "board_id": str(board_id),
                "board_name": board_name,
                "project_id": str(project_id)
            }
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting board: {str(e)}", exc_info=True)
        raise