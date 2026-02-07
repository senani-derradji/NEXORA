from influxdb_client.client.write_api import SYNCHRONOUS
from time_series.client.client import InfluxClient
from time_series.models.device_health_model import InfluxHealthModel
from time_series.config.settings import TSBS_INFO

def WriteHealthStatus(dv_name: str, dv_ip: str, dv_mac: str, type_: str = None,
                      status: bool = None, latency: float = None, packet_loss_percent: float = None,
                      cpu_usage: float = None, ram_usage: float = None, disk_usage: float = None,
                      in_bytes: float = None, out_bytes: float = None,
                      in_packets: float = None, out_packets: float = None,
                      in_errors: float = None, out_errors: float = None,
                      st: str = None
                      ):

    HEALTH_MODEL = InfluxHealthModel()
    WRITE_API = InfluxClient().client.write_api(write_options=SYNCHRONOUS)

    RESULTS = WRITE_API.write(
                        bucket=TSBS_INFO.BUCKET,
                        org=TSBS_INFO.ORGANIZATION,
                        record=HEALTH_MODEL.device_health_point(
                                            device_name=dv_name,
                                            device_type=type_,
                                            device_ip=dv_ip,
                                            device_mac=dv_mac,
                                            cpu_usage=cpu_usage,
                                            ram_usage=ram_usage,
                                            disk_usage=disk_usage,
                                            in_bytes=in_bytes,
                                            out_bytes=out_bytes,
                                            in_packets=in_packets,
                                            out_packets=out_packets,
                                            in_errors=in_errors,
                                            out_errors=out_errors,
                                            status=status,
                                            latency=latency,
                                            packet_loss_percent=packet_loss_percent,
                                            site=st
                                        )
                            )

    return RESULTS