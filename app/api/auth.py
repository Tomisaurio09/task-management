# app/api/auth.py
from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserRegisterSchema, UserResponseSchema
from app.core.dependencies import get_db
from app.services import auth_service

router = APIRouter(tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED,response_model=UserResponseSchema)
def register(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    return auth_service.register_user(user_data, db)

@router.post("/login")
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.authenticate_user(credentials.username, credentials.password, db)

@router.post("/refresh")
def refresh(refresh_token: str = Body(..., embed=True)):
    return auth_service.refresh_access_token(refresh_token)