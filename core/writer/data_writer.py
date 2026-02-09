import os, sys ; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from time_series.writers.device_health_writer import WriteHealthStatus
from core.writer.metadata_writer import DeviceMetadata
from relational.operations.devices_ops import DeviceOperations
from core.alert_engine.CoreAlertEngine import AlertEngine


class CoreWriter:

    def __init__(self):
        self.metadata = DeviceMetadata()
        self.deviceOPS = DeviceOperations()
        self.alertEngine = AlertEngine()


    def write_in_db(self, metric):

        if metric is None:
            print("METRIC IS NONE")
            return None

        payload = {
            "hostname": metric.get("hostname"),
            "device_type": metric.get("type") or "unknown",
            "ip_address": metric.get("ip_address"),
            "mac_address": metric.get("mac_address"),
            "status": metric.get("status"),
        }

        self.deviceOPS.create_device(
            hostname=payload["hostname"],
            device_type=payload.get("device_type", "unknown"),
            ip_address=payload["ip_address"],
            mac_address=payload["mac_address"],
            status=payload["status"]
        )
        self.alertEngine.Engine(
            status=payload["status"],
            hostname=payload["hostname"],

            cpu=metric.get("cpu"),
            ram=metric.get("ram"),
            disk=metric.get("disk"),

            latency=metric.get("latency"),
            packet_loss_percent=metric.get("packet_loss_percent"),

            in_bytes=metric.get("in_bytes"),
            out_bytes=metric.get("out_bytes"),
            in_packets=metric.get("in_packets"),
            out_packets=metric.get("out_packets"),
            in_errors=metric.get("in_errors"),
            out_errors=metric.get("out_errors"),
        )


        result = WriteHealthStatus(
            dv_name=metric.get("hostname"),
            dv_ip=metric.get("ip_address"),
            dv_mac=metric.get("mac_address"),
            status=metric.get("status"),
            type_=metric.get("device_type"),


            cpu_usage=metric.get("cpu"),
            ram_usage=metric.get("ram"),
            disk_usage=metric.get("disk"),

            in_bytes=metric.get("in_bytes"),
            out_bytes=metric.get("out_bytes"),
            in_packets=metric.get("in_packets"),
            out_packets=metric.get("out_packets"),
            in_errors=metric.get("in_errors"),
            out_errors=metric.get("out_errors"),

            latency=metric.get("latency"),
            packet_loss_percent=metric.get("packet_loss_percent"),

            st=metric.get("site")
        )

        return result

