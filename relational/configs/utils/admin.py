import os,sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import inspect
from relational.configs.database import engine, sessionLocal as SessionLocal
from relational.configs.database import base as Base
from relational.models.user import User
from backend.security.password import hash_password
from datetime import datetime



admins = ["admin@nexora", "derradji@nexora"]

def create_supper_user(password: str = "admin"):
    # inspector = inspect(engine)
    # tables = inspector.get_table_names()

    # if not tables:
    #     Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    for email in admins:
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            continue

        admin = User(
            email=email,
            hashed_password=hash_password(password) if password else hash_password("admin"),
            role="admin",
            last_seen=datetime.utcnow()
        )

        session.add(admin)
        session.commit()
        session.refresh(admin)

    session.close()
