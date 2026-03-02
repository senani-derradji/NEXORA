import asyncio
from engines.engine_virtual import VirtualEngine
from scheduler.heartbeat import DeviceHeartbeat
from normalizer.normalizer import Normalizer
from utils.default_data import down_metric
from transport.check_core_health import CoreHealth
from buffer.buffer_manager import BufferManager
from transport.grpc_client import CoreClient
from utils.devices_ import DeviceBootstrapper


class Scheduler:
    def __init__(self, devices_file="config/devices.yml"):
        self.host = "core"
        self.port = 50051
        self.devices_file = devices_file
        self.bootstrapper = DeviceBootstrapper(yaml_path=devices_file)
        self.devices = self.bootstrapper.check_dbs_exists_and_matched_with_yaml()

        if not self.devices:
            raise ValueError("Devices file not found or empty")

        self.engine = VirtualEngine()
        self.buffer = BufferManager()
        self.CoreClient = CoreClient(host=self.host, port=self.port)
        self.tasks = {}

    async def run_device(self, device):
        interval = device.get("interval", 5)
        while True:
            alive = DeviceHeartbeat.is_alive(device["hostname"])
            if not alive:
                normalized = Normalizer.normalize(down_metric(device=device))
            else:
                raw_metrics = self.engine.collect(
                    device_hostname=device["hostname"],
                    device_type=device["device_type"],
                    device_ip_address=device["ip_address"],
                    device_mac_address=device["mac_address"]
                )

                if raw_metrics.get("latency") > 200 or raw_metrics.get("packet_loss") > 5 or raw_metrics.get("cpu") > 85:
                    raw_metrics["status"] = "DEGRADED"
                else:
                    raw_metrics["status"] = "UP"

                normalized = Normalizer.normalize(raw_metrics)

            if CoreHealth.check(host=self.host, port=self.port, timeout=3):
                self.buffer.push_data(metric=normalized, status=True)
                get = self.buffer.pop_data()
                
                resp = self.CoreClient.send_metric(metric=get)

                if not resp:
                    self.buffer.push_data(metric=normalized, status=False)
            else:
                self.buffer.push_data(metric=normalized, status=False)

            await asyncio.sleep(interval)


    async def start(self):
        asyncio.create_task(self.sync_devices_loop())
        await self.spawn_tasks()
        await asyncio.Event().wait()


    async def spawn_tasks(self):
        for device in self.devices:
            mac = device["mac_address"]
            if mac not in self.tasks:
                self.tasks[mac] = asyncio.create_task(self.run_device(device))


    async def sync_devices_loop(self):
        while True:
            await asyncio.sleep(10)

            new_devices = self.bootstrapper.check_dbs_exists_and_matched_with_yaml()

            old_set = {d["mac_address"] for d in self.devices}
            new_set = {d["mac_address"] for d in new_devices}

            if old_set != new_set:
                self.devices = new_devices
                for mac in list(self.tasks.keys()):
                    if mac not in new_set:
                        self.tasks[mac].cancel()
                        del self.tasks[mac]

                await self.spawn_tasks()
