# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Notification API Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 3000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URL: str = ""
    
    # Queue Configuration
    EXCHANGE_NAME: str = "notifications.direct"
    EMAIL_QUEUE: str = "email.queue"
    PUSH_QUEUE: str = "push.queue"
    FAILED_QUEUE: str = "failed.queue"
    EMAIL_PRIORITY_QUEUE: str = "email.priority.queue"
    PUSH_PRIORITY_QUEUE: str = "push.priority.queue"
    
    # Service URLs
    USER_SERVICE_URL: str = "http://localhost:3001"
    TEMPLATE_SERVICE_URL: str = "http://localhost:3002"
    
    # Authentication
    API_KEY_HEADER: str = "X-API-Key"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_ENABLED: bool = True
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    
    # Notification Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    NOTIFICATION_TTL_SECONDS: int = 86400  # 24 hours
    
    # Idempotency
    IDEMPOTENCY_TTL_SECONDS: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
