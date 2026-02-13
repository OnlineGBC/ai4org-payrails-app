from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EventLogResponse(BaseModel):
    id: str
    event_type: str
    source: str
    payload: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
