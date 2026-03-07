from sqlalchemy import Column, Integer, String, DateTime
from nexora_db.configs.database import base
from datetime import datetime


class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")
    last_seen = Column(DateTime, default=datetime.utcnow())

