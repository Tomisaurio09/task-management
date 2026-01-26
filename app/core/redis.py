# app/core/redis.py
import redis
from app.core.config import settings
from app.core.logger import logger

# Redis client singleton
redis_client = None


def get_redis_client():
    """Get or create Redis client singleton"""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            # Return None if Redis is not available (graceful degradation)
            redis_client = None
    
    return redis_client


def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")