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


class DeviceCreateForm(BaseModel):
    hostname: str = Field(..., min_length=2, max_length=50)
    device_type: str = Field(..., min_length=2, max_length=30)
    ip_address: str = Field(..., min_length=7, max_length=15)
    mac_address: str = Field(..., min_length=17, max_length=17)


class DeviceUpdateForm(BaseModel):
    hostname: Optional[str] = Field(None, min_length=2, max_length=50)
    device_type: Optional[str] = Field(None, min_length=2, max_length=30)
    ip_address: Optional[str] = Field(None, pattern=r"^\d{1,3}(\.\d{1,3}){3}$")