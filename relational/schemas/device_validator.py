from pydantic import BaseModel, field_validator
from .utils import device_status, devices_groups, devices_types
from typing import Optional

class DeviceValidate(BaseModel):
    name: str = "unknown"
    device_type: str
    @field_validator('device_type')
    @staticmethod
    def validate_name(cls):
        if cls not in devices_types: raise ValueError("Invalid device type")
        return cls

    ip_address: str = "unknown"
    location: str = "unknown"

    status: str
    @field_validator("status")
    @staticmethod
    def validate_status(cls):
        if cls not in device_status:
            raise ValueError("Invalid device status")
        return cls

    group_id: Optional[int] = None


class DeviceGroupValidate(BaseModel):
    name: str
    @field_validator("name")
    @staticmethod
    def validate_name(cls):
        if cls not in devices_groups:
            raise ValueError("Invalid group name")
        return cls

    descreption: Optional[str] = None

