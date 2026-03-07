from nexora_db.models.user import User
from nexora_db.schema.validator import UserCreate
from nexora_db.configs.database import get_db
import re


class UserOperations:

    def __init__(self):
        self.db = next(get_db())

    def create_user(self, email: str, hashed_password: str):
        try:
            user = User(email=email, hashed_password=hashed_password)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_user_by_email(self, email: str):
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            raise e
        finally:
            self.db.close()

    def get_all_users(self):
        try:
            return self.db.query(User).all()
        except Exception as e:
            raise e
        finally:
            self.db.close()

    def delete_user(self, user_id: int):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            self.db.delete(user)
            self.db.commit()
            return user
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def update_user(self, user_id: int, data: UserCreate):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            user.email = data.email
            user.hashed_password = data.password
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()


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

        return email.split("@")[0].lower()