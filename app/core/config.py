# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    # JWT
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAX_PROJECTS_PER_USER: int
    DEFAULT_PAGE_SIZE:int
    MAX_PAGE_SIZE:int
    
    # CORS
    ALLOWED_ORIGINS: list[str]
    
    # App
    APP_NAME: str 
    DEBUG: bool
    
    #Redis
    REDIS_URL: str
    RATE_LIMIT_ENABLED: bool
    CACHE_TTL_DEFAULT: int
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Singleton para evitar leer .env múltiples veces"""
    return Settings()

settings = get_settings()