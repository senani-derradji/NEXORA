import os,sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from backend.api.routes import alerts, auth, users, devices
from relational.configs.utils.admin import create_supper_user
from relational.models.user import User
from relational.models.devices_model import Device
from relational.models.alerts_model import Alerts
from relational.configs.database import init_db



app = FastAPI(
    title="NEXORA Backend API",
    version="0.1.0",
    description="Backend API for Nexora Observability Platform"
)

@app.on_event("startup")
def on_startup():
    print("STARTUP ...........................")
    init_db()
    create_supper_user(password="admin")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "nexora-backend"}

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

