from influxdb_client.client.write_api import SYNCHRONOUS
from ..client.client import InfluxClient
from ..models.system_stats_model import InfluxDeviceStatsModel
from ..config.settings import TSBS_INFO

def WriteSystemStatsUsage(
                            dv_host: str, dv_type: str, dv_ip: str, dv_mac: str,
                            cpu_use: float, ram_use: float = None, disk_use: float = None,
                            st: str = None
                        ):

    SYSTEM_MODEL = InfluxDeviceStatsModel()
    WRITE_API = InfluxClient().client.write_api(write_options=SYNCHRONOUS)

    RESULTS = WRITE_API.write(
                        bucket=TSBS_INFO.BUCKET,
                        org=TSBS_INFO.ORGANIZATION,
                        record=SYSTEM_MODEL.device_sys_point(
                                            device_hostname=dv_host,
                                            device_type=dv_type,
                                            device_ip=dv_ip,
                                            device_mac=dv_mac,
                                            cpu_usage=cpu_use,
                                            ram_used=ram_use,
                                            disk_usage=disk_use,
                                            site=st
                                        )
                            )

    return RESULTS