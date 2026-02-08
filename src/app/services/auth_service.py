# app/services/auth_service.py
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User
from app.schemas.user_schema import UserRegisterSchema, UserResponseSchema
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.core.logger import logger
from app.core.redis import get_redis_client
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionsError
)

def register_user(user_data: UserRegisterSchema, db: Session) -> UserResponseSchema:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning( "User registration attempted with existing email", extra={"email": user_data.email} )
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
        
        logger.info(
            "New user registered",
            extra={
                "user_id": str(new_user.id),
                "email": new_user.email, 
                "full_name": new_user.full_name 
            } 
        )
        return new_user
    except Exception as e:
        db.rollback()
        logger.error( "Error registering user", extra={"email": user_data.email}, exc_info=True )
        raise

def authenticate_user(email: str, password: str, db: Session) -> dict:
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password):
        logger.warning( "Invalid login attempt", extra={"email": email} )
        raise InvalidCredentialsError("Invalid email or password")
    
    if not user.is_active:
        logger.warning( "Inactive user login attempt", extra={"user_id": str(user.id), "email": user.email} )
        raise InsufficientPermissionsError("User account is inactive")
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info( 
        "User logged in", 
        extra={
            "user_id": str(user.id), 
            "email": user.email
        } 
    )
       
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str) -> dict:
    payload = verify_token(refresh_token, expected_type="refresh")
    if not payload:
        logger.warning("Invalid refresh token used")
        raise InvalidCredentialsError("Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    new_access_token = create_access_token(data={"sub": user_id})
    logger.info( "Access token refreshed", extra={"user_id": str(user_id)} )
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


def logout(token: str) -> None:
    """
    Logout by adding token to blacklist in Redis.
    
    The token will be blacklisted until it expires naturally.
    """
    payload = verify_token(token, expected_type="access")
    if not payload:
        logger.warning("Logout attempt with invalid token")
        raise InvalidCredentialsError("Invalid or expired token")
    
    user_id = payload.get("sub")
    exp = payload.get("exp")
    
    if not exp:
        logger.warning("Token payload missing expiration")
        raise InvalidCredentialsError("Invalid token")
    
    redis_client = get_redis_client()
    if redis_client:
        # Calculate TTL (time until token expiration)
        import time
        ttl = max(0, int(exp - time.time()))
        
        if ttl > 0:
            # Add token to blacklist with TTL equal to token expiration
            blacklist_key = f"token_blacklist:{token[:20]}"
            redis_client.setex(blacklist_key, ttl, user_id)
            logger.info(
                "User logged out - token blacklisted",
                extra={"user_id": user_id, "ttl": ttl}
            )
        else:
            logger.info("Token already expired", extra={"user_id": user_id})
    else:
        logger.warning("Redis unavailable - logout without blacklist", extra={"user_id": user_id})