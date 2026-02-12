# app/api/auth.py
from fastapi import APIRouter, Depends, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.schemas.user_schema import UserRegisterSchema, UserResponseSchema
from app.core.dependencies import get_db, get_current_user, oauth2_scheme
from app.services import auth_service

router = APIRouter(tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED,response_model=UserResponseSchema)
@limiter.limit("5/minute")
def register(request: Request,user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    return auth_service.register_user(user_data, db)

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request,credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.authenticate_user(credentials.username, credentials.password, db)

@router.post("/refresh")
def refresh(refresh_token: str = Body(..., embed=True)):
    return auth_service.refresh_access_token(refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user=Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Logout endpoint that blacklists the current token.
    
    The token will be added to a blacklist in Redis and rejected for future use
    until it naturally expires.
    """
    auth_service.logout(token)
