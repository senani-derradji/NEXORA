from fastapi import FastAPI, HTTPException
from operations.devices_ops import DeviceOperations
from operations.alerts_ops import AlertOperations
from operations.users_service import UserOperations

device_ops = DeviceOperations()
alert_ops = AlertOperations()
users_ops = UserOperations()

app = FastAPI(title="Nexora Relational Service")



@app.get("/health")
def health():
    return {"status": "relational ok"}



@app.get("/users")
def get_users():
    result = users_ops.get_all_users()
    return {"users": result or []}

@app.get("/users/{user_email}")
def get_user(user_email: str):
    result = users_ops.get_user_by_email(user_email)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": result}

@app.post("/users")
def create_user(email: str, password: str):
    user = users_ops.create_user(email=email, hashed_password=password)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"user": user}

@app.put("/users/{user_id}")
def update_user(user_id: int, email: str, password: str):
    user = users_ops.update_user(user_id, {"email": email, "password": password})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    user = users_ops.delete_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}



@app.get("/devices")
def get_devices():
    return {"devices": device_ops.get_all_devices()}

@app.get("/devices/{mac_address}")
def get_device(mac_address: str):
    result = device_ops.get_device_by_mac_address(mac_address)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"device": result}

@app.post("/devices")
def create_device(hostname: str, device_type: str, ip_address: str, mac_address: str):
    device = device_ops.create_device(hostname, device_type, ip_address, mac_address)
    if not device:
        raise HTTPException(status_code=400, detail="Device already exists")
    return {"device": device}

@app.put("/devices/{mac_address}")
def update_device(mac_address: str, hostname: str = None, device_type: str = None, ip_address: str = None):
    data = {"hostname": hostname, "device_type": device_type, "ip_address": ip_address}
    device = device_ops.update_device(mac_address, data)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or update failed")
    return {"device": device}

@app.delete("/devices/{mac_address}")
def delete_device(mac_address: str):
    result = device_ops.delete_device(mac_address)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "Device deleted"}



@app.get("/alerts")
def get_alerts():
    return {"alerts": alert_ops.get_all_alerts() or []}

@app.get("/alerts/{device_hostname}")
def get_alerts_by_device(device_hostname: str):
    result = alert_ops.get_alerts_by_device_hostname(device_hostname)
    if not result:
        raise HTTPException(status_code=404, detail="No alerts found for this device")
    return {"alerts": result}

@app.get("/alerts/type/{alert_level}")
def get_alerts_by_type(alert_level: str):
    result = alert_ops.get_all_alerts_by_type(alert_level)
    if not result:
        raise HTTPException(status_code=404, detail="No alerts found for this type")
    return {"alerts": result}

@app.post("/alerts")
def create_alert(alert_message: str, alert_level: str, device_id: int):
    alert = alert_ops.create_alert(alert_message, alert_level, device_id)
    if not alert:
        raise HTTPException(status_code=400, detail="Alert creation failed")
    return {"alert": alert}