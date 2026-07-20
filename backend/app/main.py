from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.models import *  # noqa: F401,F403 — register all models
from app.routers import auth, payments, merchants, webhooks, consumer, wallet_transfer
from app.routers import stablecoin_webhooks, stablecoin_worker, stablecoin_api
from app.routers.merchants import banks_router

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
app.include_router(banks_router)
app.include_router(webhooks.router)
app.include_router(consumer.router)
app.include_router(wallet_transfer.router)
app.include_router(stablecoin_webhooks.router)
app.include_router(stablecoin_worker.router)
app.include_router(stablecoin_api.router)


@app.on_event("startup")
def on_startup():
    _seed_default_bank_config()
    _seed_stablecoin_balances_if_enabled()


def _seed_stablecoin_balances_if_enabled():
    import logging
    from sqlalchemy.exc import OperationalError, ProgrammingError

    if not settings.SEED_STABLECOIN_BALANCES:
        return
    from app.services.stablecoin_seed import seed_stablecoin_balances

    db = SessionLocal()
    try:
        result = seed_stablecoin_balances(db)
        logging.getLogger("payrails").info("Seeded stablecoin balances: %s", result)
    except (OperationalError, ProgrammingError) as exc:
        db.rollback()
        logging.getLogger("payrails").warning("Skipping stablecoin balance seed: %s", exc)
    finally:
        db.close()


def _seed_default_bank_config():
    import logging
    from decimal import Decimal

    from sqlalchemy.exc import OperationalError, ProgrammingError

    from app.models.bank_config import BankConfig

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
    except (OperationalError, ProgrammingError) as exc:
        # Schema not migrated yet (e.g., a fresh database in CI/tests before
        # Alembic has run). This best-effort convenience seed must never crash
        # app startup, so log and skip.
        db.rollback()
        logging.getLogger("payrails").warning(
            "Skipping default bank-config seed: %s", exc
        )
    finally:
        db.close()


@app.get("/")
def health():
    return {"status": "ok"}
