from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..configs.database import base
from datetime import datetime


class Alerts(base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_level = Column(String(10), nullable=False)
    alert_time = Column(DateTime, default=datetime.utcnow())

    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    device = relationship("Device", back_populates="alerts")

