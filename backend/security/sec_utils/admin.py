from sqlalchemy import inspect
from backend.security.password import hash_password
from datetime import datetime


admins = ["admin@nexora", "derradji@nexora"]

def create_supper_user(password: str = "admin"):


    for email in admins:

        admin = User(
            email=email,
            hashed_password=hash_password(password) if password else hash_password("admin"),
            role="admin",
            last_seen=datetime.utcnow()
        )

