from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service Info
    service_name: str = "push-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    
    # RabbitMQ Configuration
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_push_queue: str = "push.queue"
    rabbitmq_failed_queue: str = "failed.queue"
    rabbitmq_exchange: str = "notifications.direct"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    
    # Firebase Configuration
    firebase_credentials_path: str = "firebase-credentials.json"
    
    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60  # seconds
    circuit_breaker_recovery_timeout: int = 30
    
    # Retry Settings
    max_retry_attempts: int = 3
    retry_initial_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    retry_exponential_base: float = 2.0
    
    # Performance Settings
    max_concurrent_messages: int = 100
    message_prefetch_count: int = 10
    
    # Idempotency
    idempotency_ttl: int = 86400  # 24 hours in seconds
    
    # Logging
    log_level: str = "INFO"
    
    # Gateway Service URL (for status updates)
    api_gateway_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()