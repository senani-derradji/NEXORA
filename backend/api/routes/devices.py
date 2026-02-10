from fastapi import APIRouter, Depends, HTTPException
from relational.operations.devices_ops import DeviceOperations
from backend.security.jwt import require_role
from backend.schema.validator import DeviceUpdateForm

device_ops = DeviceOperations()
router = APIRouter()

@router.get("/")
def list_devices(user: dict = Depends(require_role("admin"))):
    return device_ops.get_all_devices()

@router.get("/{device_hostame}")
def get_device(device_hostame: str, user: dict = Depends(require_role("admin"))):
    return device_ops.get_device_by_hostname(hostname=device_hostame)



@router.put("/{device_hostname}")
def update_device_api(
    device_hostname: str,
    device_form: DeviceUpdateForm,
    user: dict = Depends(require_role("admin"))
    ):

    data = device_form.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    result = device_ops.update_device(device_hostname=device_hostname, data=data)

    if result is False:
        raise HTTPException(status_code=404, detail="Device not found")

    if isinstance(result, str):
        raise HTTPException(status_code=500, detail=result)

    return {"status": "updated", "device": result}




