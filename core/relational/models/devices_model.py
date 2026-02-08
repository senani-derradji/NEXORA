from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from core.relational.configs.database import base
from datetime import datetime


class Device(base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(20), unique=True)
    device_type = Column(String(10))
    ip_address = Column(String(15), unique=True)
    mac_address = Column(String(30) , unique=True)
    status = Column(String(10))
    last_seen = Column(DateTime, default=datetime.utcnow())

    alerts_device = relationship("Alerts", back_populates="device", cascade="all, delete-orphan")