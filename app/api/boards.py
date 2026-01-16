# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.board_schema import BoardCreateSchema, BoardUpdateSchema, BoardResponseSchema
from ..db.dependencies import get_db
from ..models.board import Board
from ..models.membership import UserRole  
from sqlalchemy.orm import Session
from ..auth.oauth2 import get_current_user
from ..auth.roles import check_project_role

router = APIRouter(tags=["boards"] )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BoardResponseSchema)
def create_board(
    project_id: UUID,
    board_details: BoardCreateSchema = Body(...),
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
        db.query(Board.position)
        .filter(Board.project_id == project_id)
        .order_by(Board.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0
    new_board = Board(
        name=board_details.name,
        project_id=project_id,
        position=next_position
    )
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    return new_board

@router.get("/", response_model=list[BoardResponseSchema])
def get_boards(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    boards = (
        db.query(Board)
        .filter(Board.project_id == project_id, Board.archived == False)
        .order_by(Board.position.asc())
        .all()
    )
    return boards

@router.get("/archived", response_model=list[BoardResponseSchema])
def get_archived_boards(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER],
        db=db
    )

    boards = (
        db.query(Board)
        .filter(Board.project_id == project_id, Board.archived == True)
        .order_by(Board.position.asc())
        .all()
    )
    return boards

@router.get("/{board_id}", response_model=BoardResponseSchema)
def get_board(
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

    board = (
        db.query(Board)
        .filter(Board.id == board_id, Board.project_id == project_id)
        .first()
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found.")
    return board

@router.patch("/{board_id}", response_model=BoardResponseSchema)
def update_board(
    project_id: UUID,
    board_id: UUID,
    board_details: BoardUpdateSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],
        db=db
    )

    board = (
        db.query(Board)
        .filter(Board.id == board_id, Board.project_id == project_id)
        .first()
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found.")

    if board_details.name is not None:
        board.name = board_details.name
    if board_details.position is not None:
        board.position = board_details.position
    if board_details.archived is not None:
        board.archived = board_details.archived
    
    db.commit()
    db.refresh(board)
    return board

@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    project_id: UUID,
    board_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_role(
        project_id=project_id,
        user_id=current_user["id"],
        allowed_roles=[UserRole.OWNER, UserRole.EDITOR],
        db=db
    )

    board = (
        db.query(Board)
        .filter(Board.id == board_id, Board.project_id == project_id)
        .first()
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found.")

    db.delete(board)
    db.commit()
    return None