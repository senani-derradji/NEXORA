from fastapi import APIRouter, Depends, HTTPException
from nexora_db.operations.devices_ops import DeviceOperations
from security.jwt import require_role, get_current_user
from nexora_db.schema.validator import DeviceUpdateForm, DeviceCreateForm
from config import init ; init(url_env="DATABASE_URL")
from datetime import datetime, timezone
from utils.logger import setup_logger
from time_series_readers.influx_reader import get_influx_reader
import yaml, os, sys
from pathlib import Path


# Setup logger
logger = setup_logger('backend.devices', level=20)

device_ops = DeviceOperations()
router = APIRouter()

# Path to devices.yml in collectors config (mounted volume in container)
SHARED_DEVICES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "collectors", "config", "devices.yml")
logger.info(f"SHARED_DEVICES_PATH initialized to: {SHARED_DEVICES_PATH}")

def remove_device_from_yaml_by_ip(DEVICES_FILE: Path, ip_address: str):
    logger.info(f"remove_device_from_yaml_by_ip called with IP: {ip_address}, file: {DEVICES_FILE}")
    if not os.path.exists(DEVICES_FILE):
        raise Exception("devices.yml not found")

    with open(DEVICES_FILE, "r") as f:
        data = yaml.safe_load(f)

    logger.info(f"Loaded YAML data: {data}")

    if not isinstance(data, dict) or "devices" not in data or not isinstance(data["devices"], list):
        raise Exception("Invalid YAML format: expected {'devices': [...]}")

    devices = data["devices"]
    logger.info(f"Current devices in YAML: {devices}")

    new_devices = [d for d in devices if d.get("ip_address") != ip_address]
    logger.info(f"Devices after filtering by IP {ip_address}: {new_devices}")

    if len(devices) == len(new_devices):
        logger.warning(f"No device found with IP {ip_address} in YAML")
        return False  # nothing removed

    data["devices"] = new_devices

    with open(DEVICES_FILE, "w") as f:
        yaml.safe_dump(data, f)

    logger.info(f"Successfully removed device with IP {ip_address} from YAML")
    return True



def _sync_device_to_yaml(device_data: dict, action: str = "add"):
    """
    Sync device to shared devices.yml for collectors.
    action: 'add' to add device, 'remove' to remove device
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(SHARED_DEVICES_PATH), exist_ok=True)

        # Load existing devices
        if os.path.exists(SHARED_DEVICES_PATH):
            with open(SHARED_DEVICES_PATH, "r") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {"devices": []}

        devices = data.get("devices", [])

        if action == "add":
            # Check if device already exists (by mac_address)
            device_exists = any(d.get("mac_address") == device_data.get("mac_address") for d in devices)
            if not device_exists:
                devices.append(device_data)
                logger.info(f"Added device {device_data.get('hostname')} to devices.yml")
            else:
                logger.warning(f"Device {device_data.get('hostname')} already exists in devices.yml")
        elif action == "remove":
            # Remove device by ip_address (primary) or mac_address (fallback)
            ip_to_remove = device_data.get("ip_address")
            mac_to_remove = device_data.get("mac_address")
            original_count = len(devices)
            devices = [d for d in devices if d.get("ip_address") != ip_to_remove]
            if len(devices) == original_count and mac_to_remove:
                # Fallback: try to remove by mac_address if IP didn't match
                devices = [d for d in devices if d.get("mac_address") != mac_to_remove]
            if len(devices) < original_count:
                logger.info(f"Removed device with IP {ip_to_remove} from devices.yml")
            else:
                logger.warning(f"Device with IP {ip_to_remove} not found in devices.yml")

        # Save updated devices
        data["devices"] = devices
        with open(SHARED_DEVICES_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    except Exception as e:
        logger.error(f"Failed to sync device to YAML: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync device: {str(e)}")

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

def _get_device_metrics():
    """Get metrics for all devices from InfluxDB"""
    try:
        reader = get_influx_reader()
        fields = ['cpu_usage', 'ram_usage', 'disk_usage', 'latency']
        data = reader.get_latest_values(fields)

        # Organize data by device hostname
        devices_data = {}
        for item in data:
            device_name = item.get('device')
            if not device_name:
                continue

            if device_name not in devices_data:
                devices_data[device_name] = {}

            field = item.get('field')
            value = item.get('value')

            # Include all values (including zeros) for device metrics
            if field and value is not None:
                try:
                    devices_data[device_name][field] = float(value)
                except (ValueError, TypeError):
                    pass

        return devices_data
    except Exception as e:
        logger.warning(f"Failed to get device metrics: {e}")
        return {}

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

    # Sync device to shared devices.yml for collectors
    device_data = {
        "ip_address": device.ip_address,
        "hostname": device.hostname,
        "device_type": device.device_type,
        "mac_address": device.mac_address,
        "status": device.status or "unknown",
        "interval": device.interval or 5
    }
    _sync_device_to_yaml(device_data, action="add")
    logger.info(f"Device {device.hostname} created and synced to collectors")

    return { "status": "created", "device": {"hostname": device.hostname} }


@router.get("/")
def list_devices(user: dict = Depends(_require_admin_or_viewer())):
    devices = device_ops.get_all_devices()

    # Get metrics from InfluxDB
    device_metrics = _get_device_metrics()

    # Serialize devices to JSON
    device_list = []
    for d in devices:
        # Get metrics for this device
        metrics = device_metrics.get(d.hostname, {})

        device_list.append({
            "id": d.id,
            "hostname": d.hostname,
            "device_type": d.device_type,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "status": _is_device_online(d),
            "status_text": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "interval": d.interval,
            "cpu_usage": metrics.get('cpu_usage'),
            "ram_usage": metrics.get('ram_usage'),
            "disk_usage": metrics.get('disk_usage'),
            "latency": metrics.get('latency')
        })

    return device_list


@router.get("/{device_mac_address}")
def get_device(device_mac_address: str, user: dict = Depends(_require_admin_or_viewer())):
    device = device_ops.get_device_by_mac_address(mac_address=device_mac_address)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Get metrics from InfluxDB
    device_metrics = _get_device_metrics()
    metrics = device_metrics.get(device.hostname, {})

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
            "interval": device.interval,
            "cpu_usage": metrics.get('cpu_usage'),
            "ram_usage": metrics.get('ram_usage'),
            "disk_usage": metrics.get('disk_usage'),
            "latency": metrics.get('latency')
        }
    }


@router.delete("/{device_mac_address}")
def delete_device(device_mac_address: str, user: dict = Depends(require_role("admin"))):
    logger.info(f"Delete request received for device: {device_mac_address}")
    logger.info(f"User attempting delete: {user}")

    device = device_ops.get_device_by_mac(mac_address=device_mac_address)

    if not device:
        logger.warning(f"Device not found: {device_mac_address}")
        raise HTTPException(status_code=404, detail="Device not found")

    logger.info(f"Device found: {device.hostname}")

    device_ip = device.ip_address
    logger.warning(f"Device IP: {device_ip}")

    delete_result = device_ops.delete_device(mac_address=device_mac_address)

    if not delete_result:
        logger.error(f"Failed to delete device: {device_mac_address}")
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        logger.info(f"Device IP to remove from YAML: {device_ip}")
        logger.info(f"YAML file path: {SHARED_DEVICES_PATH}")
        logger.info(f"YAML file exists: {os.path.exists(SHARED_DEVICES_PATH)}")

        # Read current YAML content for debugging
        if os.path.exists(SHARED_DEVICES_PATH):
            with open(SHARED_DEVICES_PATH, "r") as f:
                yaml_content = yaml.safe_load(f)
            logger.info(f"Current YAML devices: {yaml_content}")

        yaml_result = remove_device_from_yaml_by_ip(ip_address=device_ip, DEVICES_FILE=SHARED_DEVICES_PATH)
        logger.info(f"YAML removal result: {yaml_result}")
    except Exception as e:
        logger.error(f"YAML sync failed: {str(e)}")

    logger.info(f"Device {device.hostname} deleted from database and devices.yml")

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

