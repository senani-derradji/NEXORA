from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from security.jwt import get_current_user, require_role
from nexora_db.operations.users_service import UserOperations

router = APIRouter()
user_ops = UserOperations()

class UserUpdate(BaseModel):
    email: str = None
    username: str = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.get("/me")
def read_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": user.get("id", 0),
        "email": user.get("email"),
        "role": user.get("role"),
        "username": user.get("email", "").split("@")[0] if user.get("email") else ""
    }

@router.put("/me")
def update_me(user_data: UserUpdate, user: dict = Depends(get_current_user)):
    return {
        "id": user.get("id", 0),
        "email": user_data.email or user.get("email"),
        "role": user.get("role"),
        "username": user_data.username or user.get("email", "").split("@")[0] if user.get("email") else ""
    }

@router.post("/change-password")
def change_password(password_data: PasswordChange, user: dict = Depends(get_current_user)):
    """Change user password"""
    user = user_ops.get_user_by_email(user.get("email"))



    return {"message": "Password changed successfully"}

# @router.get("/admin-only")
# def admin_only_route(user: dict = Depends(require_role("admin"))):
#     return {"msg": f"Hello {user['email']}! You are admin."}

# Admin-only user management endpoints
@router.get("/")
def list_users(user: dict = Depends(require_role("admin"))):

    users = user_ops.get_all_users()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return {"users": users}

@router.delete("/{user_id}")
def delete_user(user_id: int, user: dict = Depends(require_role("admin"))):
    """Delete a user - admin only"""
    user_deleted_status = user_ops.delete_user(user_id)
    if user_deleted_status is None:
        raise HTTPException(status_code=404, detail="User not found")
    if isinstance(user_deleted_status, str):
        raise HTTPException(status_code=500, detail=user_deleted_status)
    if user_ops.get_user_by_email(user_deleted_status.email) is not None:
        raise HTTPException(status_code=500, detail="User not deleted")

    return {"message": f"User {user_id} deleted successfully"}
