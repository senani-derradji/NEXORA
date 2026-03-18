from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from nexora_db.configs.database import base
from datetime import datetime, timezone


class Alerts(base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_message = Column(String(100), nullable=False)
    alert_level = Column(String(10), nullable=False)
    alert_time = Column(DateTime, default=datetime.utcnow)

    device_id = Column(Integer, ForeignKey("device.id"), nullable=True)
    device = relationship("Device", back_populates="alerts_device")