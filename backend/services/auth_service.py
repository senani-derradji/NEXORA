from security.password import hash_password, verify_password
from security.jwt import create_access_token
from nexora_db.operations.users_service import UserOperations

user_operations = UserOperations()


def register_user(email, password):
    user = user_operations.create_user(email, hash_password(password))
    return user


def authenticate_user(email: str, password: str):
    user = user_operations.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def login_user(user):
    return create_access_token({"sub": user.email , "role": user.role})
