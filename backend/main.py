

from fastapi import FastAPI
from api.routes import alerts, auth, users, devices
from utils.admin import create_supper_user
from nexora_db.models.user import User
from nexora_db.models.devices_model import Device
from nexora_db.models.alerts_model import Alerts
from config import init


app = FastAPI(
    title="NEXORA Backend API",
    version="0.2.0",
    description="Backend API for Nexora Observability Platform"
)

@app.on_event("startup")
def on_startup():
    print("STARTUP !!")
    init(url_env="DATABASE_URL")
    create_supper_user(password="admin")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "nexora-backend"}

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

