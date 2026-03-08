import os, sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from core.configs.database import init ; init()
from nexora_db.operations.devices_ops import DeviceOperations


class DeviceMetadata:
    def __init__(self):
        self.deviceOPS = DeviceOperations()


    def write_device_metadata(self, payload):
        if not payload:
            return False

        hostname = payload.get("hostname")
        device_type = payload.get("device_type")
        ip_address = payload.get("ip_address")
        mac_address = payload.get("mac_address")
        status = payload.get("status")

        self.deviceOPS.create_device(
            hostname=hostname,
            device_type=device_type,
            ip_address=ip_address,
            mac_address=mac_address,
            status=status
        )
        return True