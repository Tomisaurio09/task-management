# app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings
from app.core.redis import get_redis_client
from app.core.logger import logger


def get_identifier_from_request(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Prioritizes authenticated user ID over IP address.
    """
    # Try to get user from token
    # Si el user esta autenticado, usa su user id como identificador
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # Sino, usa la direccion IP
    return get_remote_address(request)


# Guarda un contador en el redis para "contar las peticiones"
limiter = Limiter(
    key_func=get_identifier_from_request,
    storage_uri=settings.REDIS_URL if settings.RATE_LIMIT_ENABLED else None,
    enabled=settings.RATE_LIMIT_ENABLED,
    strategy="fixed-window",  # or "moving-window" for more accuracy
)


def get_limiter():
    """Get the rate limiter instance"""
    return limiter