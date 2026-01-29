from influxdb_client.client.write_api import SYNCHRONOUS
from ..client.client import InfluxClient
from ..models.device_health_model import InfluxHealthModel
from ..config.settings import TSBS_INFO

def WriteHealthStatus(dv_name: str, dv_ip: str, dv_mac: str,
                      status: bool, latency: float = None, packet_loss_percent: float = None,
                      st: str = None
                    ):

    HEALTH_MODEL = InfluxHealthModel()
    WRITE_API = InfluxClient().client.write_api(write_options=SYNCHRONOUS)

    RESULTS = WRITE_API.write(
                        bucket=TSBS_INFO.BUCKET,
                        org=TSBS_INFO.ORGANIZATION,
                        record=HEALTH_MODEL.device_health_point(
                                            device_name=dv_name,
                                            device_ip=dv_ip,
                                            device_mac=dv_mac,
                                            status=status,
                                            latency=latency,
                                            packet_loss_percent=packet_loss_percent,
                                            site=st
                                        )
                            )

    return RESULTS