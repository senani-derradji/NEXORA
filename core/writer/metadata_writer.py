import os, sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from relational.operations.devices_ops import DeviceOperations



class DeviceMetadata:
    def __init__(self):
        self.deviceOPS = DeviceOperations()


    def write_device_metadata(self, payload):
        if not payload:
            print("INSIDE WRITE DEVICE METADATA : PAYLOAD IS EMPTY")
            return False

        hostname = payload.get("hostname")
        device_type = payload.get("device_type")
        ip_address = payload.get("ip_address")
        mac_address = payload.get("mac_address")
        status = payload.get("status")

        print(hostname, device_type, ip_address, mac_address, status)


        self.deviceOPS.create_device(
            hostname=hostname,
            device_type=device_type,
            ip_address=ip_address,
            mac_address=mac_address,
            status=status
        )
        return True