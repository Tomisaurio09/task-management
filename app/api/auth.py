from fastapi import APIRouter, Depends, status, HTTPException, Response
from ..schemas.user_schema import UserRegisterSchema, UserLoginSchema
from ..db.dependencies import get_db
from sqlalchemy.orm import Session
from ..models.user import User

router = APIRouter(tags=["auth"])

@router.post("/login")
def login(user: UserLoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )