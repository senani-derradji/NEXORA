import asyncio
import logging
from engines.snmp_engine.snmp_collector import SNMPConfig, SNMPMonitor
from normalizer.normalizer import Normalizer
from scheduler.heartbeat import DeviceHeartbeat
from utils.default_data import down_metric
from transport.check_core_health import CoreHealth
from buffer.buffer_manager import BufferManager
from transport.grpc_client import CoreClient
from utils.devices_ import DeviceBootstrapper
from engines.snmp_engine.utils.detect_vendor import detect_vendor
from engines.snmp_engine.utils.detect_type import detect_device_type

# Create logger for collector
logger = logging.getLogger('nexora.collector')


class Scheduler:
    def __init__(self, devices_file="config/devices.yml"):
        self.host = "core"
        self.port = 50051
        self.devices_file = devices_file
        self.bootstrapper = DeviceBootstrapper(yaml_path=devices_file)
        self.devices = self.bootstrapper.check_dbs_exists_and_matched_with_yaml()

        if not self.devices:
            raise ValueError("Devices file not found or empty")

        self.buffer = BufferManager()
        self.config = SNMPConfig(community="public", port=161, timeout=2, retries=1, mp_model=1)
        self.snmp_collector = SNMPMonitor(config=self.config)
        self.CoreClient = CoreClient(host=self.host, port=self.port)


        self.tasks = {}

    async def run_device(self, device):
        interval = device.get("interval", 5)

        while True:
            # alive = DeviceHeartbeat.is_alive(device["hostname"])
            # if not alive:
            #     normalized = Normalizer.normalize(down_metric(device=device))
            try:
                # Run blocking SNMP operations in thread pool for concurrent execution
                raw_metrics = await asyncio.to_thread(
                    self.snmp_collector.collect_metrics_as_dataclass,
                    hostname=device["hostname"],
                    device_type=device["device_type"],
                    ip=device["ip_address"],
                    mac_placeholder=device["mac_address"]
                )

                # Set status to DOWN or UP
                if raw_metrics.get("status") == "down":
                    raw_metrics["status"] = "DOWN"
                else:
                    raw_metrics["status"] = "UP"

                # Always send status to core (even when device is DOWN) so database gets updated
                # For DOWN devices, we send minimal data (status only, metrics are None/0)
                normalized = Normalizer.normalize(raw_metrics)

                # Run blocking SNMP GET in thread pool
                self.sys_object_id = await asyncio.to_thread(
                    self.snmp_collector.snmp_get,
                    ip=device["ip_address"],
                    oid=self.snmp_collector.OID_SYS_OBJECT_ID
                )

                vendor = detect_vendor(self.sys_object_id)
                device_type = detect_device_type(self.sys_object_id)

                logger.info(f"[{device['hostname']}] Metrics collected successfully - Vendor: {vendor}, Type: {device_type}")

                # Run gRPC send in thread pool to avoid blocking
                if CoreHealth.check(host=self.host, port=self.port, timeout=3):
                    self.buffer.push_data(metric=normalized, status=True)
                    get = self.buffer.pop_data()

                    resp = await asyncio.to_thread(self.CoreClient.send_metric, metric=get)

                    if not resp:
                        self.buffer.push_data(metric=normalized, status=False)
                else:
                    self.buffer.push_data(metric=normalized, status=False)

            except Exception as e:
                logger.error(f"[{device['hostname']}] Error collecting metrics: {e}")
                import traceback
                traceback.print_exc()

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