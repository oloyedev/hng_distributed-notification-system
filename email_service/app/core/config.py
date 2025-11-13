from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
  
    APP_NAME: str 
    VERSION: str 
    DEBUG: bool 
    HOST: str
    PORT: int 
    
    # Redis
    REDIS_HOST: str 
    REDIS_PORT: int
    REDIS_DB: int 
    REDIS_PASSWORD: str 
    REDIS_URL: str 
    
    # RabbitMQ
    RABBITMQ_HOST: str 
    RABBITMQ_PORT: int 
    RABBITMQ_USER: str 
    RABBITMQ_PASSWORD: str 
    RABBITMQ_VHOST: str 
    RABBITMQ_URL: str 
    
    # Queue Configuration
    EXCHANGE_NAME: str 
    EMAIL_QUEUE: str 
    EMAIL_PRIORITY_QUEUE: str 
    FAILED_QUEUE: str 
    
    # Email Configuration
    SMTP_HOST: str 
    SMTP_PORT: int 
    SMTP_USER: str 
    SMTP_PASSWORD: str 
    SMTP_FROM_EMAIL: str 
    SMTP_FROM_NAME: str 
    SMTP_USE_TLS: bool 
    
    # SendGrid (alternative)
    SENDGRID_API_KEY: str 
    USE_SENDGRID: bool 
    
    # Template Service
    TEMPLATE_SERVICE_URL: str 
    
    # API Gateway
    API_GATEWAY_URL: str 
    
    # Service Token for authentication
    SERVICE_NAME: str 
    SERVICE_TOKEN: str 
    
    # Retry Configuration
    MAX_RETRIES: int 
    RETRY_DELAY_SECONDS: int 
    EXPONENTIAL_BACKOFF: bool 
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int 
    CIRCUIT_BREAKER_TIMEOUT: int 
    
    # Performance
    PREFETCH_COUNT: int 
    CONCURRENT_WORKERS: int 
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()