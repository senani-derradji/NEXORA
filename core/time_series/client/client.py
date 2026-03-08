from influxdb_client import InfluxDBClient
from core.time_series.config.settings import TSBS_INFO
from core.time_series.client.healthcheck import credentials_is_valid


class InfluxClient:

    def __init__(self):
        if credentials_is_valid():
            self.client = InfluxDBClient(
                                url=TSBS_INFO.URL or "http://influxdb:8086",
                                token=TSBS_INFO.TOKEN,
                                org=TSBS_INFO.ORGANIZATION or "myorg"
                                     )
        else:
            print("[Credentials] ** Credentials are not valid !( **")