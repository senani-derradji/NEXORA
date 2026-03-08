from influxdb_client import Point
from influxdb_client.client.exceptions import InfluxDBError
from core.time_series.models.main_model import InfluxMainModel


class InfluxHealthModel:

    def device_health_point(
                  self,
                  device_name: str, device_ip: str, device_mac: str, cpu_usage: float, ram_usage: float,
                  disk_usage: float = None, device_type: str = None,
                  in_bytes: float = None, out_bytes: float = None,
                  in_packets: float = None, out_packets: float = None,
                  in_errors: float = None, out_errors: float = None,
                  status: bool = 0, latency: float = None, packet_loss_percent: float = None,
                  site: str = None,
                  timestamp=None
                  ) -> Point:

        point = InfluxMainModel().device_main_point(
                                            device_name=device_name,
                                            device_ip=device_ip,
                                            device_mac=device_mac,
                                            device_type=device_type,
                                            site=site,
                                            timestamp=timestamp
                                        )

        if status is None or latency is None:
            raise InfluxDBError("DEVICE STATUS MISSING")

        if status is not None:
            point = point.field("status", status)

        if latency is not None:
            point = point.field("latency", latency)

        if packet_loss_percent is not None:
            point = point.field("packet_loss_percent", packet_loss_percent)

        if cpu_usage is not None:
            point = point.field("cpu_usage", cpu_usage)

        if ram_usage is not None:
            point = point.field("ram_usage", ram_usage)

        if disk_usage is not None:
            point = point.field("disk_usage", disk_usage)

        if in_bytes is not None:
            point = point.field("in_bytes", in_bytes)

        if out_bytes is not None:
            point = point.field("out_bytes", out_bytes)

        if in_packets is not None:
            point = point.field("in_packets", in_packets)

        if out_packets is not None:
            point = point.field("out_packets", out_packets)

        if in_errors is not None:
            point = point.field("in_errors", in_errors)

        if out_errors is not None:
            point = point.field("out_errors", out_errors)

        return point







