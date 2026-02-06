import asyncio
from collectors.engines.engine_virtual import VirtualEngine
from collectors.utils.devices_ import OpenMetricsInformer
from collectors.scheduler.heartbeat import DeviceHeartbeat
from collectors.normalizer.normalizer import Normalizer
from collectors.utils.default_data import down_metric
from collectors.transport.check_core_health import CoreHealth
from collectors.buffer.buffer_manager import BufferManager
from collectors.transport.grpc_client import CoreClient



class Scheduler:
    def __init__(self, devices_file="collectors/config/devices.yml"):
        self.devices = OpenMetricsInformer._load_devices(devices_file)
        if not self.devices:
            raise ValueError("Devices file not found or empty")

        self.engine = VirtualEngine()
        self.buffer = BufferManager()

    async def run_device(self, device):
        interval = device.get("interval", 5)

        while True:
            alive = DeviceHeartbeat.is_alive(device["hostname"])

            if not alive:
                normalized = Normalizer.normalize(down_metric(device=device))

            else:
                raw_metrics = self.engine.collect(
                    device_hostname=device["hostname"],
                    device_type=device["type"],
                    device_ip_address=device["ip_address"],
                    device_mac_address=device["mac_address"]
                )

                if raw_metrics.get("latency") > 200 or raw_metrics.get("packet_loss") > 5 or raw_metrics.get("cpu") > 85:
                    raw_metrics["status"] = "DEGRADED"
                else: raw_metrics["status"] = "UP"

                normalized = Normalizer.normalize(raw_metrics)

            if CoreHealth.check(host="localhost", port=50051, timeout=2):
                print("CORE IS HEALTHY : TRANSFER DATA TO MEMORY ")
                "CORE CHECKED : ON"
                self.buffer.push_data(metric=normalized, status=True) ; get = self.buffer.pop_data()
                resp = CoreClient().send_metric(metric=get)
                if not resp:
                    self.buffer.push_data(metric=normalized, status=False)

            else:
                "CORE CHECKED : OFF"
                print("CORE IS NOT HEALTHY : TRANSFER DATA TO DISK ")

                self.buffer.push_data(metric=normalized, status=False)

            await asyncio.sleep(interval)


    async def start(self):
        tasks = [asyncio.create_task(self.run_device(device)) for device in self.devices]
        await asyncio.gather(*tasks)