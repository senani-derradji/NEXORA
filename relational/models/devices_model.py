from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from relational.configs.database import base
from datetime import datetime
from sqlalchemy.orm import validates


class Device(base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(20), unique=True, nullable=False)
    device_type = Column(String(10))
    ip_address = Column(String(15), unique=True, nullable=False)
    mac_address = Column(String(30) , unique=True, nullable=False)
    status = Column(String(10))
    interval = Column(Integer, default=5)
    last_seen = Column(DateTime, default=datetime.utcnow())

    alerts_device = relationship("Alerts", back_populates="device", cascade="all, delete-orphan")

    @validates("mac_address")
    def validate_mac(self, key, value):
        if self.mac_address is not None:
            raise ValueError("mac_address cannot be changed once set")
        return value