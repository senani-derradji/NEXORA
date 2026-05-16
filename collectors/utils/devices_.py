import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.exc import IntegrityError

from collectors.config.db_config.database import init
from nexora_db.operations.devices_ops import DeviceOperations

init(url_env="DATABASE_URL")

class DeviceBootstrapper:

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.device_ops = DeviceOperations()


    def _load_yaml_devices(self):

        if not os.path.exists(self.yaml_path):
            return []

        with open(self.yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            return []

        devices = data.get("devices")

        if not isinstance(devices, list):
            return []

        normalized_devices = []
        for d in devices:
            if isinstance(d, str):
                normalized_devices.append({
                    "ip_address": d,
                    "hostname": "unknown",
                    "mac_address": "00:00:00:00:00:00",
                    "device_type": "unknown",
                    "interval": 5
                })
            elif isinstance(d, dict):
                d.setdefault("hostname", "unknown")
                d.setdefault("mac_address", "00:00:00:00:00:00")
                d.setdefault("device_type", "unknown")
                d.setdefault("interval", 5)
                normalized_devices.append(d)

        return normalized_devices


    def _load_db_devices(self):

        devices = self.device_ops.get_all_devices()

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


    def compare(self):

        yaml_devices = self._load_yaml_devices()
        db_devices = self._load_db_devices()

        yaml_macs = {d["mac_address"] for d in yaml_devices}
        db_macs = {d["mac_address"] for d in db_devices}

        print(yaml_macs == db_macs, " COMPARED (TRUE = SAME , FALSE = DIFFERENT)")

        return yaml_macs == db_macs


    def check_dbs_exists_and_matched_with_yaml(self):

        yaml_devices = self._load_yaml_devices()
        db_devices = self._load_db_devices()

        db_macs = {d["mac_address"] for d in db_devices}

        if self.compare():
            return db_devices

        for device in yaml_devices:

            if device["mac_address"] in db_macs:
                continue

            try:

                self.device_ops.create_device(
                    hostname=device["hostname"],
                    device_type=device["device_type"],
                    ip_address=device["ip_address"],
                    mac_address=device["mac_address"],
                    status="START",
                    interval=device.get("interval", 5),
                )

                print(f"[BOOTSTRAP] Added device {device['hostname']}")

            except IntegrityError:

                print(f"[BOOTSTRAP] Device already exists: {device['hostname']}")

        return self._load_db_devices()