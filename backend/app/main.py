from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, SessionLocal
from app.models import *  # noqa: F401,F403 — register all models
from app.database import Base
from app.routers import auth, payments, merchants, webhooks, consumer

app = FastAPI(title="PayRails Backend")

origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(merchants.router)
app.include_router(webhooks.router)
app.include_router(consumer.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_default_bank_config()


def _seed_default_bank_config():
    from app.models.bank_config import BankConfig
    from decimal import Decimal

    db = SessionLocal()
    try:
        existing = db.query(BankConfig).filter(BankConfig.bank_name == "MockBank").first()
        if not existing:
            config = BankConfig(
                bank_name="MockBank",
                supported_rails="fednow,rtp,ach,card",
                fednow_limit=Decimal("500000"),
                rtp_limit=Decimal("1000000"),
                ach_limit=Decimal("10000000"),
                is_active=True,
            )
            db.add(config)
            db.commit()
    finally:
        db.close()


@app.get("/")
def health():
    return {"status": "ok"}
