from fastapi import APIRouter, Depends
from backend.security.jwt import get_current_user, require_role

router = APIRouter()

@router.get("/me")
def read_me(user: dict = Depends(get_current_user)):
    return user

@router.get("/admin-only")
def admin_only_route(user: dict = Depends(require_role("admin"))):
    return {"msg": f"Hello {user['email']}! You are admin."}