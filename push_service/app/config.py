from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Info
    service_name: str 
    service_version: str
    environment: str 
    
    # API Settings
    api_host: str 
    api_port: int 
    
    # RabbitMQ Configuration
    rabbitmq_host: str 
    rabbitmq_port: int 
    rabbitmq_user: str 
    rabbitmq_password: str 
    rabbitmq_vhost: str
    rabbitmq_push_queue: str 
    rabbitmq_failed_queue: str
    rabbitmq_exchange: str 
    
    # Redis Configuration
    redis_host: str 
    redis_port: int 
    redis_db: int 
    redis_password: str
    
    # Firebase Configuration
    firebase_credentials_path: str 
    
    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: float
    circuit_breaker_timeout: float
    circuit_breaker_recovery_timeout:float
    
    # Retry Settings
    max_retry_attempts: int 
    retry_initial_delay: float    # seconds
    retry_max_delay: float # seconds
    retry_exponential_base: float 
    
    # Performance Settings
    max_concurrent_messages: int 
    message_prefetch_count: int 
    
    # Idempotency
    idempotency_ttl: int # 24 hours in seconds
    
    # Logging
    log_level: str 
    
    # Gateway Service URL (for status updates)
    api_gateway_url: str 
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()