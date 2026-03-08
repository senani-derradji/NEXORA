from fastapi import APIRouter
from nexora_db.operations.alerts_ops import AlertOperations
from config import init ; init(url_env="DATABASE_URL")

alert_ops = AlertOperations()
router = APIRouter()

@router.get("/")
def all_alerts():
    alerts = alert_ops.get_all_alerts()

    if not alerts:
        return "Alerts Doesn't Exists :("

    if len(alerts) > 100:
        return "Too many alerts +100"

    return alerts


@router.get("/{device_hostname}")
def get_alerts(device_hostname: str):
    alerts = alert_ops.get_alerts_by_device_hostname(device_hostname)

    if not alerts:
        return "Alert Doesn't Exists :("

    return alerts


@router.delete("/{device_hostname}")
def delete_alert(device_hostname: str):
    alert_del = alert_ops.delete_alerts_by_device_hostname(device_hostname)

    if not alert_del:
        return "Alert Doesn't Exists :("

    return {"status": f"alert deleted successfully for {device_hostname}"}
