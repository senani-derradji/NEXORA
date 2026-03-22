from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class SqlMetrics(Base):
    __tablename__ = "buffer_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device = Column(String)
    metric_type = Column(String)
    ots = Column(Float)
    sent = Column(Boolean, default=False)
    payload = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))