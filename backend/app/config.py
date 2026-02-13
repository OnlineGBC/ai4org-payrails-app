from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./local.db"
    CORS_ORIGINS: str = "*"
    ENCRYPTION_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
