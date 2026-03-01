import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from configs.database import init_db, sessionLocal
from operations.devices_ops import DeviceOperations
from models.devices_model import Device


class DeviceBootstrapper:
    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.device_ops = DeviceOperations()

    def _load_yaml_devices(self):
        if not os.path.exists(self.yaml_path):
            return []
        with open(self.yaml_path, "r") as f:
            return (yaml.safe_load(f) or {}).get("devices", [])

    def _load_db_devices(self):
        db = sessionLocal()
        try:
            devices = db.query(Device).all()
            return [
                {
                    "hostname": d.hostname,
                    "device_type": d.device_type,
                    "ip_address": d.ip_address,
                    "mac_address": d.mac_address,
                    "status": d.status,
                    "interval": d.interval,
                }
                for d in devices
            ]
        finally:
            db.close()

    def compare(self):
        yaml_devices = self._load_yaml_devices()
        db_devices = self._load_db_devices()

        yaml_set = {d["mac_address"] for d in yaml_devices}
        db_set = {d["mac_address"] for d in db_devices}

        return yaml_set == db_set

    def check_dbs_exists_and_matched_with_yaml(self):
        init_db()

        yaml_devices = self._load_yaml_devices()
        db_devices = self._load_db_devices()

        if not db_devices:
            for device in yaml_devices:
                self.device_ops.create_device(
                    hostname=device["hostname"],
                    device_type=device["device_type"],
                    ip_address=device["ip_address"],
                    mac_address=device["mac_address"],
                    status="START",
                    interval=device.get("interval"),
                )

            db_devices = self._load_db_devices()

        if not self.compare():
            print("MAC_ADDRESS mismatch between YAML and DB")

        return db_devices