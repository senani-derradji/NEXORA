from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from nexora_db.configs.database import get_db
from nexora_db.schema.validator import UserCreate
from services.auth_service import register_user, authenticate_user, login_user
from fastapi.security import OAuth2PasswordRequestForm
from nexora_db.operations.users_service import UserUtils

router = APIRouter()

@router.post("/register")
def register(data: UserCreate):
    user = register_user(email=data.email, password=data.password)
    return {"username": UserUtils.get_username_from_email(data.email), "email": user.email}

@router.post("/login")
def login(form_data = Depends(OAuth2PasswordRequestForm), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    print(f"USER : {user}")

    token = login_user(user)

    return {
            "access_token": f"{token}",
            "token_type": "bearer"
            }