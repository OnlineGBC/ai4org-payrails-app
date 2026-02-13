import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models.event_log import EventLog


def log_event(
    db: Session,
    event_type: str,
    source: str,
    reference_id: Optional[str] = None,
    payload: Optional[dict] = None,
):
    event = EventLog(
        event_type=event_type,
        source=source,
        reference_id=reference_id,
        payload=json.dumps(payload) if payload else None,
    )
    db.add(event)
    db.commit()
    return event
