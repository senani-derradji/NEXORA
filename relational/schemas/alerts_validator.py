from pydantic import BaseModel, field_validator
from .utils import alert_levels

class AlertValidate(BaseModel):
    alert_level: str
    alert_message: str = "unknown"

    @field_validator("alert_level")
    @staticmethod
    def validate_alert_level(cls):
        if cls not in alert_levels:
            raise ValueError("Invalid alert level")
        return cls

    device_id: int = None