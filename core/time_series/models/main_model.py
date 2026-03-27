from influxdb_client import Point
from core.time_series.client.client import InfluxClient


class InfluxMainModel:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = InfluxClient().client
        return cls._client

    def device_main_point(
                  self,
                  device_name: str, device_ip: str, device_mac: str, device_type: str = None,
                  timestamp=None,
                  site: str = None,
            ) -> Point:

        point = Point("DEVICE_STATS_V1")

        point = point \
            .tag("device_name", device_name) \
            .tag("device_ip", device_ip) \
            .tag("device_mac", device_mac) \
            .tag("device_type", device_type)


        if timestamp is not None:
            point = point.time(timestamp, write_precision="ms")

        if site is not None:
            point = point.tag("site", site)


        return point