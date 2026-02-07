from influxdb_client import InfluxDBClient
from time_series.config.settings import TSBS_INFO
from time_series.client.healthcheck import credentials_is_valid


class InfluxClient:

    def __init__(self):
        if credentials_is_valid():
            self.client = InfluxDBClient(
                                url=TSBS_INFO.URL,
                                token=TSBS_INFO.TOKEN,
                                org=TSBS_INFO.ORGANIZATION
                                     )
