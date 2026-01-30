from influxdb_client import Point
from influxdb_client.client.exceptions import InfluxDBError
from .main_model import InfluxMainModel


class InfluxNetworkModel:

    def device_net_point(
                  self,
                  device_hostname: str, device_type: str, device_ip: str, device_mac: str, # CORE DEVICE INFORMATION
                  in_bytes: float = None, out_bytes: float = None,  # CORE NETWORK INFORMATION
                  in_packets: int = None, out_packets: int = None,  # CORE NETWORK INFORMATION
                  in_errors: int = None, out_errors: int = None,  # CORE NETWORK INFORMATION
                  in_drops: int = None, out_drops: int = None,  # CORE NETWORK INFORMATION
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

        if in_bytes is None or out_bytes is None or in_packets is None or out_packets is None:
            raise InfluxDBError("NETWORK INFORMATION MISSING")

        point = point \
            .field("in_bytes", in_bytes) \
            .field("out_bytes", out_bytes) \
            .field("in_packets", in_packets) \
            .field("out_packets", out_packets) \
            .field("in_errors", in_errors) \
            .field("out_errors", out_errors) \
            .field("in_drops", in_drops) \
            .field("out_drops", out_drops)


        return point







