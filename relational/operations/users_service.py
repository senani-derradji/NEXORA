import os, sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from relational.configs.database import sessionLocal as SessionLocal
from relational.models.user import User
from backend.schema.validator import UserCreate



class UserOperations:

    def __init__(self):
        self.db = SessionLocal()

    def create_user(self, email: str, hashed_password: str):
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_all_users(self):
        return self.db.query(User).all()

    def delete_user(self, user_id: int):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        self.db.delete(user)
        self.db.commit()
        return user

    def update_user(self, user_id: int, data: UserCreate):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.email = data.email
        user.hashed_password = data.password
        self.db.commit()
        self.db.refresh(user)
        return user




class UserUtils:

    @staticmethod
    def get_username_from_email(email):
        if "@" in email:
            return email.split("@")[0]
        return email

