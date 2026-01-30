from influxdb_client.client.write_api import SYNCHRONOUS
from ..client.client import InfluxClient
from ..models.network_traffic_model import InfluxNetworkModel
from ..config.settings import TSBS_INFO

def WriteNetworkTraffic(dv_host: str, dv_type: str, dv_ip: str, dv_mac: str,
                        in_bytes: float = None, out_bytes: float = None,
                        in_packets: int = None, out_packets: int = None,
                        in_errors: int = None, out_errors: int = None,
                        in_drops: int = None, out_drops: int = None,
                        st: str = None
                        ):

    NETWORK_MODEL = InfluxNetworkModel()
    WRITE_API = InfluxClient().client.write_api(write_options=SYNCHRONOUS)

    RESULTS = WRITE_API.write(
                        bucket=TSBS_INFO.BUCKET,
                        org=TSBS_INFO.ORGANIZATION,
                        record=NETWORK_MODEL.device_net_point(
                                            device_hostname=dv_host,
                                            device_type=dv_type,
                                            device_ip=dv_ip,
                                            device_mac=dv_mac,
                                            in_bytes=in_bytes,
                                            out_bytes=out_bytes,
                                            in_packets=in_packets,
                                            out_packets=out_packets,
                                            in_errors=in_errors,
                                            out_errors=out_errors,
                                            in_drops=in_drops,
                                            out_drops=out_drops,
                                            site=st
                                        )
                            )

    return RESULTS