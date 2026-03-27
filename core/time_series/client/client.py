from influxdb_client import InfluxDBClient
from core.time_series.config.settings import TSBS_INFO
from core.time_series.client.healthcheck import credentials_is_valid


class InfluxClient:

    def __init__(self):
        print(f"[DEBUG] InfluxClient.__init__() called")
        self.client = None
        if credentials_is_valid():
            print(f"[DEBUG] Credentials are valid, creating InfluxDBClient")
            try:
                self.client = InfluxDBClient(
                                    url=TSBS_INFO.URL or "http://influxdb:8086",
                                    token=TSBS_INFO.TOKEN,
                                    org=TSBS_INFO.ORGANIZATION or "myorg"
                                         )
                print(f"[DEBUG] InfluxDBClient created successfully with client attribute")
            except Exception as e:
                print(f"[ERROR] Failed to create InfluxDBClient: {e}")
                self.client = None
        else:
            print("[ERROR] Credentials are not valid! InfluxClient will not have a 'client' attribute!")
            print(f"[ERROR] URL: {TSBS_INFO.URL}")
            print(f"[ERROR] TOKEN: {TSBS_INFO.TOKEN[:10]}..." if TSBS_INFO.TOKEN else "[ERROR] TOKEN: None or empty")
            print(f"[ERROR] ORGANIZATION: {TSBS_INFO.ORGANIZATION}")