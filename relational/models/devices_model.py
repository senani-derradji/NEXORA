from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..configs.database import base
from datetime import datetime


class Device(base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    device_type = Column(String(10), nullable=False)
    ip_address = Column(String(15), unique=True)
    location = Column(String(10))
    status = Column(String(10), nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow())

    group_id = Column(Integer, ForeignKey("devices_groups.id"), nullable=True)
    group = relationship("DevicesGroup", back_populates="devices")

    alerts_device = relationship("Alerts", back_populates="device", cascade="all, delete-orphan")


class DevicesGroup(base):
    __tablename__ = "devices_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), unique=True)
    description = Column(String(100))

    devices = relationship("Device", back_populates="group", cascade="all, delete-orphan")