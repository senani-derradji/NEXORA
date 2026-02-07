from influxdb_client import InfluxDBClient
from ..config.settings import TSBS_INFO
from .healthcheck import credentials_is_valid


class InfluxClient:

    """
    InfluxClient is a wrapper class for managing the InfluxDB connection.
    It ensure the credentials are valid before creating the client.
    checking the org / bucket existence | create if not exist
    """

    def __init__(self):
        if credentials_is_valid():
            self.client = InfluxDBClient(
                                url=TSBS_INFO.URL,
                                token=TSBS_INFO.TOKEN,
                                org=TSBS_INFO.ORGANIZATION
                                     )
