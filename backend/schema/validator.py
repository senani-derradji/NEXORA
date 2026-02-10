from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        orm_mode = True


class DeviceUpdateForm(BaseModel):
    hostname: Optional[str] = Field(None, min_length=2, max_length=50)
    device_type: Optional[str] = Field(None, min_length=2, max_length=30)
    ip_address: Optional[str] = Field(None, pattern=r"^\d{1,3}(\.\d{1,3}){3}$")
    mac_address: Optional[str] = Field(None, pattern=r"^[0-9A-Fa-f:]{17}$")
