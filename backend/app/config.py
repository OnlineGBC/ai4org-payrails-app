from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./local.db"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:5000,http://localhost:8000"
    ENCRYPTION_KEY: str = ""
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "noreply@payrails.test"
    BREVO_SENDER_NAME: str = "PayRails"
    BREVO_SMS_SENDER: str = "PayRails"
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
