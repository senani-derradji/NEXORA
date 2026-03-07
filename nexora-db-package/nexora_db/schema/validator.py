from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&* ...).")
        return v


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    model_config = {
        "from_attributes": True
    }


class DeviceCreateForm(BaseModel):
    hostname: str = Field(..., min_length=2, max_length=50)
    device_type: str = Field(..., min_length=2, max_length=30)
    ip_address: str = Field(..., min_length=7, max_length=15)
    mac_address: str = Field(..., min_length=17, max_length=17)

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IP address format. Expected format: 192.168.1.1")
        parts = v.split(".")
        if not all(0 <= int(p) <= 255 for p in parts):
            raise ValueError("Each octet in the IP address must be between 0 and 255.")
        return v

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Expected format: AA:BB:CC:DD:EE:FF")
        return v.upper()



class DeviceUpdateForm(BaseModel):
    hostname: Optional[str] = Field(None, min_length=2, max_length=50)
    device_type: Optional[str] = Field(None, min_length=2, max_length=30)
    ip_address: Optional[str] = Field(None)

    @field_validator("ip_address", mode="before")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IP address format. Expected format: 192.168.1.1")
        parts = v.split(".")
        if not all(0 <= int(p) <= 255 for p in parts):
            raise ValueError("Each octet in the IP address must be between 0 and 255.")
        return v