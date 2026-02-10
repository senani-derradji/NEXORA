from fastapi import APIRouter
from relational.operations.alerts_ops import AlertOperations

alert_ops = AlertOperations()
router = APIRouter()

@router.get("/")
def query_metrics():
    return alert_ops.get_all_alerts()

@router.get("/{device_hostname}")
def get_metric(device_hostname: str):
    return alert_ops.get_alerts_by_device_hostname(device_hostname)
