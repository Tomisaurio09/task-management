# app/services/auth_service.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import UserRegisterSchema
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.core.logger import logger
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionsError
)
#SI TENGO UN ENDPOINT QUE HABLA SOBRE EL USER INACTIVE NECESITO UN
#HELPER QUE SEA UN LOGOUT Y DESPUES CREAR UN ENDPOINT CON ESO
def register_user(user_data: UserRegisterSchema, db: Session) -> User:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise UserAlreadyExistsError("User already exists")
    try:
        new_user = User(
            email=user_data.email,
            password=hash_password(user_data.password),
            full_name=user_data.full_name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {new_user.email}")
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        raise

def authenticate_user(email: str, password: str, db: Session) -> dict:
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password):
        raise InvalidCredentialsError("Invalid email or password")
    
    if not user.is_active:
        raise InsufficientPermissionsError("User account is inactive")
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str) -> dict:
    payload = verify_token(refresh_token, expected_type="refresh")
    if not payload:
        raise InvalidCredentialsError("Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    new_access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }