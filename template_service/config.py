from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST_NAME: str
    DB_PORT: int
    DB_PASSWORD: str
    DB_USERNAME: str
    DB_NAME: str
    REDIS_URL: str


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
