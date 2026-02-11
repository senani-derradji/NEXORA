import yaml, os, sys, sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from relational.configs.database import DATABASE_URL, init_db
from relational.operations.devices_ops import DeviceOperations
from relational.models.devices_model import Device
from relational.models.alerts_model import Alerts


class DeviceBootstrapper:
    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.db_path = self._get_db_path(DATABASE_URL)
        self.device_ops = DeviceOperations()


    def _get_db_path(self, db_url: str) -> str:
        return db_url.replace("sqlite:///", "") if db_url.startswith("sqlite:///") else db_url

    def _load_yaml_devices(self):
        if not os.path.exists(self.yaml_path):
            return []
        with open(self.yaml_path, "r") as f:
            return (yaml.safe_load(f) or {}).get("devices", [])

    def _load_db_devices(self, table_name="device"):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"DB not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]


    def compare(self, table_name="device"):
        yaml_devices = self._load_yaml_devices()
        db_devices = self._load_db_devices(table_name)

        yaml_set = {(d["mac_address"]) for d in yaml_devices}
        db_set = {(d["mac_address"]) for d in db_devices}

        if yaml_set == db_set:
            return True
        else:
            return False


    def check_dbs_exists_and_matched_with_yaml(self):
        if not os.path.exists(self.db_path):
            init_db()

            for self.data in self._load_yaml_devices():
                self.device_ops.create_device(
                        hostname=self.data["hostname"], device_type=self.data["device_type"],
                        ip_address=self.data["ip_address"], mac_address=self.data["mac_address"],
                        status="START", interval=self.data["interval"] if "interval" in self.data else None
                    )
            self.data = self._load_db_devices()
        else:
            self.data = self._load_db_devices()
            if not self.data:
                for self.data in self._load_yaml_devices():
                    self.device_ops.create_device(
                        hostname=self.data["hostname"], device_type=self.data["device_type"],
                        ip_address=self.data["ip_address"], mac_address=self.data["mac_address"],
                        status="START", interval=self.data["interval"] if "interval" in self.data else None
                    )
                self.data = self._load_db_devices()
            else:
                self.data = self._load_db_devices()

        if not self.compare(table_name="device"):
            print("SOMETHING (MAC_ADDRESS) ARE CHANGED IN YAML FILE / DB ; CHECK IT OUT")



        return self.data
