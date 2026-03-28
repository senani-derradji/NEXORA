

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import alerts, auth, users, devices, dashboard, metrics
from api.routes.alerts_ws import router as alerts_ws_router
from utils.admin import create_supper_user
from utils.logger import setup_logger
from nexora_db.models.devices_model import Device
from nexora_db.models.alerts_model import Alerts
from config import init

logger = setup_logger('backend.main', level=20)

app = FastAPI(
    title="NEXORA Backend API",
    version="0.2.0",
    description="Backend API for Nexora Observability Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("="*50)
    logger.info("NEXORA BACKEND STARTING UP")
    logger.info("="*50)
    init(url_env="DATABASE_URL")
    logger.info("Database initialized successfully")
    print(create_supper_user(password = "admin"))
    logger.info("Super user created/verified")
    logger.info("Backend startup complete")


@app.get("/health", tags=["system"])
def health():
    logger.debug("Health check endpoint called")
    return {"status": "ok", "service": "nexora-backend"}


@app.get("/test", tags=["system"])
def test():
    logger.info("Test endpoint called")
    return {"message": "Backend is reachable!"}

app.include_router(auth.router, prefix="/auth", tags=["auth"])
logger.info("Registered auth router at /auth")

app.include_router(users.router, prefix="/users", tags=["users"])
logger.info("Registered users router at /users")

app.include_router(devices.router, prefix="/devices", tags=["devices"])
logger.info("Registered devices router at /devices")

app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
logger.info("Registered alerts router at /alerts")

app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
logger.info("Registered dashboard router at /dashboard")

app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
logger.info("Registered metrics router at /metrics")

app.include_router(alerts_ws_router)
logger.info("Registered WebSocket router at /ws/alerts")

logger.info("All routers registered successfully")
