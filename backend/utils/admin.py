from nexora_db.configs.database import get_db
from nexora_db.models.user import User
from security.password import hash_password
from datetime import datetime
from config import init

init(url_env="DATABASE_URL")

admins = ["admin@nexora", "derradji@nexora"]

def create_supper_user(password: str = "admin"):

    session = next(get_db())

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

        print(admin, " ::: Created admin user")

    session.close()