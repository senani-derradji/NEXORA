from ..models.devices_model import Device
from ..schemas.device_validator import DeviceValidate

class DeviceOperations:
    def __init__(self, db):
        self.session = db

    def create_device(self, payload: DeviceValidate):
        device = Device(
            name=payload.name,
            device_type=payload.device_type,
            ip_address=payload.ip_address,
            location=payload.location,
            status=payload.status,
            group_id=payload.group_id
        )
        self.session.add(device)
        self.session.commit()
        self.session.refresh(device)
        return device

    def get_all_devices(self):
        return self.session.query(Device).all()

    def get_device_by_id(self, device_id: int):
        return self.session.query(Device).filter(Device.id == device_id).first()

    def update_device(self, device_id: int, payload: DeviceValidate):
        device = self.get_device_by_id(device_id)
        if not device:
            return None

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(device, key, value)

        self.session.commit()
        self.session.refresh(device)
        return device

    def delete_device(self, device_id: int):
        device = self.get_device_by_id(device_id)
        if not device:
            return False

        self.session.delete(device)
        self.session.commit()
        return True