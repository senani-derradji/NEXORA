from fastapi import APIRouter, Depends, HTTPException
from nexora_db.operations.devices_ops import DeviceOperations
from security.jwt import require_role, get_current_user
from nexora_db.schema.validator import DeviceUpdateForm, DeviceCreateForm
from config import init ; init(url_env="DATABASE_URL")
from datetime import datetime, timezone
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('backend.devices', level=20)

device_ops = DeviceOperations()
router = APIRouter()

def _is_device_online(device):
    now = datetime.now(timezone.utc)
    device_status = str(device.status).upper() if device.status else ""

    # Handle timezone-aware vs naive datetime comparison
    is_online = False
    if device_status in ["UP", "up"]:
        is_online = True
    elif device.last_seen:
        last_seen = device.last_seen
        if last_seen.tzinfo is None:
            # Naive datetime from DB - assume UTC
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if (now - last_seen).total_seconds() < 30:
            is_online = True

    return 1 if is_online else 0

def _require_admin_or_viewer():
    """Allow both admin and viewer roles"""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.get("/count")
def get_device_count():
    """Get total device count - no authentication required for standalone topology"""
    devices = device_ops.get_all_devices()
    return {"count": len(devices)}

@router.post("/create")
def create_device(user: dict = Depends(require_role("admin")), device_form = Depends(DeviceCreateForm)):
    device = device_ops.create_device(
        hostname=device_form.hostname,
        device_type=device_form.device_type,
        ip_address=device_form.ip_address,
        mac_address=device_form.mac_address
    )
    if not device:
        raise HTTPException(status_code=400, detail="Device already exists")
    return { "status": "created", "device": {"hostname": device.hostname} }


@router.get("/")
def list_devices(user: dict = Depends(_require_admin_or_viewer())):
    devices = device_ops.get_all_devices()

    # Serialize devices to JSON
    device_list = []
    for d in devices:
        device_list.append({
            "id": d.id,
            "hostname": d.hostname,
            "device_type": d.device_type,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "status": _is_device_online(d),
            "status_text": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "interval": d.interval
        })

    return device_list


@router.get("/{device_mac_address}")
def get_device(device_mac_address: str, user: dict = Depends(_require_admin_or_viewer())):
    device = device_ops.get_device_by_mac_address(mac_address=device_mac_address)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "device": {
            "id": device.id,
            "hostname": device.hostname,
            "device_type": device.device_type,
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
            "status": _is_device_online(device),
            "status_text": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "interval": device.interval
        }
    }


@router.delete("/{device_mac_address}")
def delete_device(device_mac_address: str, user: dict = Depends(require_role("admin"))):

    if not device_ops.delete_device(device_mac_address=device_mac_address):
        raise HTTPException(status_code=404, detail="Device not found")

    return {"status": "deleted"}


@router.put("/{device_mac_address}")
def update_device_api(
    device_mac_address: str,
    device_form: DeviceUpdateForm,
    user: dict = Depends(require_role("admin"))
    ):

    data = device_form.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(status_code=400, detail="No data provided")

    result = device_ops.update_device(mac_address=device_mac_address, data=data)

    if result is False:
        raise HTTPException(status_code=404, detail="Device not found")

    if isinstance(result, str):
        raise HTTPException(status_code=500, detail=result)

    return {"status": "updated", "device": result}
