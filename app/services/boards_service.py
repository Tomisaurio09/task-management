from uuid import UUID
from sqlalchemy.orm import Session
from app.models.board import Board
from app.schemas.board_schema import BoardCreateSchema, BoardUpdateSchema, BoardResponseSchema
from app.core.logger import logger
from app.core.exceptions import (
    BoardNotFoundError,
    BoardCreationError
)

def create_board(
    project_id: UUID,
    board_details: BoardCreateSchema,
    db: Session
) -> Board:
    try:
        max_position_row = db.query(Board).filter(
            Board.project_id == project_id
        ).order_by(Board.position.desc()).first()

        next_position = (max_position_row.position + 1) if max_position_row else 0
        new_board = Board(
            name=board_details.name,
            project_id=project_id,
            position=next_position
        )
        db.add(new_board)
        db.commit()
        db.refresh(new_board)
        logger.info(f"Board '{new_board.name}' created in project {project_id}")
        return new_board
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating board: {str(e)}", exc_info=True)
        raise BoardCreationError("Failed to create board") from e
    
def get_boards(project_id: UUID, include_archived: bool, db: Session) -> list[BoardResponseSchema]:
    query = db.query(Board).filter(Board.project_id == project_id)
    
    if not include_archived:
        query = query.filter(Board.archived == False)
    
    return query.order_by(Board.position.asc()).all()

def get_board_by_id(
    project_id: UUID,
    board_id: UUID,
    db: Session
) ->BoardResponseSchema:

    board = (
        db.query(Board)
        .filter(Board.id == board_id, Board.project_id == project_id)
        .first()
    )
    if not board:
        raise BoardNotFoundError(f"Board {board_id} not found in project {project_id}")
    return board

def update_board(
    project_id: UUID,
    board_id: UUID,
    board_details: BoardUpdateSchema,
    db: Session
)-> BoardResponseSchema:

    board = get_board_by_id(project_id, board_id)

    if board_details.name is not None:
        board.name = board_details.name
    if board_details.position is not None:
        board.position = board_details.position
    if board_details.archived is not None:
        board.archived = board_details.archived
    
    db.commit()
    db.refresh(board)
    logger.info(f"Board {board_id} updated")
    return board

def delete_board(
    project_id: UUID,
    board_id: UUID,
    db: Session
):

    board = get_board_by_id(project_id, board_id)

    try:
        db.delete(board)
        db.commit()
        logger.info(f"Board {board_id} deleted from project {project_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting board: {str(e)}", exc_info=True)
        raise