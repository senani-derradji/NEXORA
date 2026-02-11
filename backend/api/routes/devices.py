from fastapi import APIRouter, Depends, HTTPException
from relational.operations.devices_ops import DeviceOperations
from backend.security.jwt import require_role
from backend.schema.validator import DeviceUpdateForm, DeviceCreateForm


device_ops = DeviceOperations()
router = APIRouter()

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
def list_devices(user: dict = Depends(require_role("admin"))):
    return device_ops.get_all_devices()


@router.get("/{device_mac_address}")
def get_device(device_mac_address: str, user: dict = Depends(require_role("admin"))):
    device = device_ops.get_device_by_mac_address(mac_address=device_mac_address)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"device": device}


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