from fastapi import APIRouter, Depends, status, HTTPException, Body
from ..schemas.user_schema import UserRegisterSchema
from ..core.dependencies import get_db
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from ..models.user import User
from ..core.security import verify_password,create_access_token, create_refresh_token, verify_token
router = APIRouter(tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_details: UserRegisterSchema, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.email == user_details.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists."
        )
    hashed_password = hash(user_details.password)
    user_details.password = hashed_password

    new_user = User(
        email=user_details.email,
        password=user_details.password,
        full_name=user_details.full_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.email == user_credentials.username).first()

    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid credentials"
        )


    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_token(refresh_token: str = Body(...)):
    payload = verify_token(refresh_token, type="refresh")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    new_access_token = create_access_token(data={"sub": user_id})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
