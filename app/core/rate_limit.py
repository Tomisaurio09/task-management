# app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings



def get_identifier_from_request(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Prioritizes authenticated user ID over IP address.
    """

    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_identifier_from_request,
    storage_uri=settings.REDIS_URL if settings.RATE_LIMIT_ENABLED else None,
    enabled=settings.RATE_LIMIT_ENABLED,
    strategy="fixed-window",  
)


def get_limiter():
    """Get the rate limiter instance"""
    return limiter