from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SMTP_HOST:str
    SMTP_PORT:int
    SMTP_USER:str
    SMTP_PASSWORD:str
    EMAIL_FROM:str
    EMAIL_FROM_NAME:str
    DB_HOST_NAME:str
    DB_PORT:int
    DB_PASSWORD:str
    DB_USERNAME:str
    DB_NAME:str

    ENVIRONMENT:str
    DEBUG:bool

    RABBITMQ_HOST:str
    RABBITMQ_PORT:int
    RABBITMQ_USER:str
    RABBITMQ_PASSWORD:str
    RABBITMQ_EMAIL_QUEUE:str
    RABBITMQ_PUSH_QUEUE:str
    RABBITMQ_FAILED_QUEUE:str

    REDIS_URL:str
    REDIS_HOST:str
    REDIS_PORT:int
    REDIS_DB:int


    API_GATEWAY_URL:str
    TEMPLATE_SERVICE_URL:str
    USER_SERVICE_URL:str


    MAX_RETRY_ATTEMPTS:int
    CIRCUIT_BREAKER_FAILURE_THRESHOLD:int
    MESSAGE_PREFETCH_COUNT:int


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
