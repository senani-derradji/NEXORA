from influxdb_client import Point
from influxdb_client.client.exceptions import InfluxDBError
from .main_model import InfluxMainModel


class InfluxDeviceStatsModel:

    def device_sys_point(
                  self,
                  device_hostname: str, device_type: str, device_ip: str, device_mac: str, # CORE DEVICE INFORMATION
                  cpu_usage: float = None, ram_used: float = None, disk_usage: float = None,  # CORE SYSTEM INFORMATION
                  site: str = None,
                  timestamp=None
                  ) -> Point:

        point = InfluxMainModel().device_main_point(
                                            device_hostname=device_hostname,
                                            device_type=device_type,
                                            device_ip=device_ip,
                                            device_mac=device_mac,
                                            site=site,
                                            timestamp=timestamp
                                        )

        if cpu_usage is None or ram_used is None:
            raise InfluxDBError("SYSTEM INFORMATION MISSING")

        point = point \
            .field("cpu_usage", cpu_usage) \
            .field("ram_used", ram_used) \
            .field("disk_usage", disk_usage)

        return point