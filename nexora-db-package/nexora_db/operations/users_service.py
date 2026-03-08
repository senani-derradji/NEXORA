from nexora_db.models.user import User
from nexora_db.schema.validator import UserCreate
from nexora_db.configs.database import get_db
import re


class UserOperations:

    def create_user(self, email: str, hashed_password: str):
        db = next(get_db())
        try:
            user = User(email=email, hashed_password=hashed_password)

            db.add(user)
            db.commit()
            db.refresh(user)

            return user

        except Exception as e:
            db.rollback()
            raise e

        finally:
            db.close()


    def get_user_by_email(self, email: str):
        db = next(get_db())
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()


    def get_all_users(self):
        db = next(get_db())
        try:
            return db.query(User).all()
        finally:
            db.close()


    def delete_user(self, user_id: int):
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return None

            db.delete(user)
            db.commit()

            return user

        except Exception as e:
            db.rollback()
            raise e

        finally:
            db.close()


    def update_user(self, user_id: int, data: UserCreate):
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return None

            user.email = data.email
            user.hashed_password = data.password

            db.commit()
            db.refresh(user)

            return user

        except Exception as e:
            db.rollback()
            raise e

        finally:
            db.close()


class UserUtils:

    EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    @staticmethod
    def get_username_from_email(email: str) -> str:

        if not isinstance(email, str):
            raise TypeError(f"Expected a string, got {type(email).__name__}")

        email = email.strip()

        if not email:
            raise ValueError("Email cannot be empty")

        if not UserUtils.EMAIL_PATTERN.match(email):
            raise ValueError(f"Invalid email format: {email!r}")

        return email.split("@")[0].lower().strip()