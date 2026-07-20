"""Background-worker endpoints for stablecoin settlement and reconciliation.

Designed to be invoked by Cloud Scheduler / Cloud Tasks (not end users). Guarded
by a shared secret header (X-Worker-Secret); in production the scheduler injects
it. Fails closed when the secret is unset.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.stablecoin_service import poll_pending_settlements, run_reconciliation

router = APIRouter(prefix="/tasks", tags=["stablecoin-worker"])


def require_worker_secret(x_worker_secret: str = Header(default="")) -> None:
    expected = settings.STABLECOIN_WORKER_SECRET
    if not expected or x_worker_secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/settle", dependencies=[Depends(require_worker_secret)])
def settle(db: Session = Depends(get_db)):
    settled = poll_pending_settlements(db)
    return {"settled": settled}


@router.post("/reconcile", dependencies=[Depends(require_worker_secret)])
def reconcile(db: Session = Depends(get_db)):
    reports = run_reconciliation(db)
    drifted = [r for r in reports if not r["reconciled"]]
    return {
        "accounts": len(reports),
        "drifted": len(drifted),
        "reports": [
            {"user_id": r["user_id"], "asset_code": r["asset_code"], "drift": str(r["drift"])}
            for r in drifted
        ],
    }
