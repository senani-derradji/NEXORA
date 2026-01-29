from influxdb_client import Point
from influxdb_client.client.exceptions import InfluxDBError
from .main_model import InfluxMainModel


class InfluxHealthModel:

    def device_health_point(
                  self,
                  device_name: str, device_ip: str, device_mac: str, # CORE DEVICE INFORMATION
                  status: bool = 0, latency: float = None, packet_loss_percent: float = None,  # CORE DEVICE STATUS INFORMATION
                  site: str = None,
                  timestamp=None
                  ) -> Point:

        point = InfluxMainModel().device_main_point(
                                            device_name=device_name,
                                            device_ip=device_ip,
                                            device_mac=device_mac,
                                            site=site,
                                            timestamp=timestamp
                                        )

        if status is None or latency is None:
            raise InfluxDBError("DEVICE STATUS MISSING")

        point = point \
            .field("status", status) \
            .field("latency", latency) \
            .field("packet_loss_percent", packet_loss_percent)

        return point







