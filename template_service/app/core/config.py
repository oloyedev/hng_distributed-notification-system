# template_service/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str 
    VERSION: str 
    DEBUG: bool 
    HOST: str 
    PORT: int 
    
    # Database
    DATABASE_URL: str 
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int 
    
    # Redis
    REDIS_HOST: str 
    REDIS_PORT: int 
    REDIS_DB: int
    REDIS_PASSWORD: str 
    REDIS_URL: str 
    
    # Template Configuration
    DEFAULT_LANGUAGE: str 
    SUPPORTED_LANGUAGES: list 
    TEMPLATE_CACHE_TTL: int 
    
    # Versioning
    ENABLE_VERSIONING: bool = True
    MAX_VERSIONS_PER_TEMPLATE: int = 10
    
    # Authentication
    SERVICE_TOKEN: str 
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()