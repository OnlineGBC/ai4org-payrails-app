"""Regression tests for the app-startup default bank-config seed.

The startup event calls ``_seed_default_bank_config()`` using the real
``SessionLocal``. In a fresh environment (CI / tests before Alembic has run)
the ``bank_configs`` table may not exist yet. The seed must degrade gracefully
instead of raising, otherwise it crashes app startup and every test that spins
up the app via ``TestClient(app)`` (this was the CI "no such table: bank_configs"
failure).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main


def test_seed_default_bank_config_skips_when_table_missing(monkeypatch):
    # An empty database with NO tables created.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    EmptySession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(main, "SessionLocal", EmptySession)

    # Before the fix this raised sqlalchemy.exc.OperationalError
    # ("no such table: bank_configs"). It must now be a no-op.
    main._seed_default_bank_config()


def test_client_fixture_starts_app_cleanly(client):
    # The startup event fires when TestClient enters its context; a health
    # check confirms the app came up without the seed crashing setup.
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
