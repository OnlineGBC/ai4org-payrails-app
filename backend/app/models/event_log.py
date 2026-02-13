import uuid
from sqlalchemy import Column, String, DateTime, Text, func
from app.database import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False)
    payload = Column(Text, nullable=True)  # JSON string
    reference_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
