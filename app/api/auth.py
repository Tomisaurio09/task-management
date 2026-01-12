from fastapi import APIRouter, Depends, status, HTTPException, Response
from ..schemas.user_schema import UserRegisterSchema
from ..db.dependencies import get_db
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from ..models.user import User
from ..auth.passwords import verify, hash
from ..auth.oauth2 import create_access_token
router = APIRouter(tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_details: UserRegisterSchema, db: Session = Depends(get_db)):
    #check if user already exists
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

#login is done, now we handle register
@router.post("/login")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    #OAuth2PasswordRequestForm points to username, but we read the field as email bc username can be whatever
    user = db.query(User).filter(User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid credentials"
        )

    if not verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid credentials"
        )
    #put all the information of the user u want

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
