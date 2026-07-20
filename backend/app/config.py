from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./local.db"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:5000,http://localhost:8000,http://192.168.1.88:3000,http://192.168.1.88:8080,http://192.168.1.88:8000"
    ENCRYPTION_KEY: str = ""
    # Email via SMTP relay (Brevo or any provider)
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    FROM_ADDR: str = "noreply@payrails.test"
    SENDER_NAME: str = "PayRails"
    # SMS via Brevo REST API
    BREVO_API_KEY: str = ""
    BREVO_SMS_SENDER: str = "PayRails"
    # Claude API (AI-generated transaction descriptions)
    ANTHROPIC_API_KEY: str = ""
    # Stablecoin partner integration (step 4 async processing)
    # Secret Manager names: payrails-stablecoin-webhook-secret / -worker-secret
    STABLECOIN_WEBHOOK_SECRET: str = ""   # HMAC secret for inbound partner webhooks
    STABLECOIN_WORKER_SECRET: str = ""    # shared secret guarding /tasks/* worker endpoints
    # KYT / blockchain-analytics provider (Secret Manager: payrails-kyt-api-key)
    KYT_API_KEY: str = ""
    KYT_BASE_URL: str = ""
    # API rate limiting (per-instance, fixed window)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
