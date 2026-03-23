import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime, timezone

from core.time_series.writers.device_health_writer import WriteHealthStatus
from core.configs.database import init ; init()
from nexora_db.operations.devices_ops import DeviceOperations
from core.alert_engine.CoreAlertEngine import AlertEngine
from core.utils.logger import setup_logger

# Setup logger
logger = setup_logger('core.writer', level=20)


class CoreWriter:

    def __init__(self):
        self.deviceOPS = DeviceOperations()
        self.alertEngine = AlertEngine()
        logger.info("CoreWriter initialized")

    def write_in_db(self, metric):
        logger.debug(f"write_in_db called with metric: {metric}")

        if metric is None:
            logger.warning("METRIC IS NONE - skipping write")
            return None

        payload = {
            "hostname": metric.get("hostname"),
            "device_type": metric.get("device_type") or "unknown",
            "ip_address": metric.get("ip_address"),
            "mac_address": metric.get("mac_address"),
            "status": metric.get("status"),
        }

        logger.debug(f"Payload prepared: {payload}")

        print(f"""

PAYLOAD ::::
{payload}

              """)

        device = self.deviceOPS.get_device_by_ip(ip_address=payload["ip_address"])

        if device is None:
            # Create the device and get its ID
            new_device = self.deviceOPS.create_device(
                hostname=payload["hostname"],
                device_type=payload["device_type"],
                ip_address=payload["ip_address"],
                mac_address=payload["mac_address"],
                status=payload["status"]
            )
            # Force commit by getting a fresh session and retrieving the device
            from nexora_db.database import get_db
            session = next(get_db())
            session.commit()

            # Get the device ID after creation
            device = self.deviceOPS.get_device_by_ip(ip_address=payload["ip_address"])
            logger.info(f"[WRITER] Created new device: {payload['hostname']} with id: {device.id if device else 'unknown'}")
        else:
            print("DEVICE EXISTS (not none)")
            self.deviceOPS.update_device_status(
                ip_address=payload["ip_address"],
                status=payload["status"],
                last_seen=datetime.now(timezone.utc)
            )

        # Pass device_id to alert engine to avoid lookup issues
        if device is None:
            logger.error(f"[WRITER] FAILED to get device ID for {payload['hostname']} - alerts will not be created!")
            device_id = None
        else:
            device_id = device.id

        logger.debug(f"[WRITER] Calling AlertEngine with device_id={device_id}, hostname={payload['hostname']}")

        self.alertEngine.Engine(
            status=payload["status"],
            hostname=payload["hostname"],
            device_id=device_id,

            cpu=metric.get("cpu"),
            ram=metric.get("ram"),
            disk=metric.get("disk"),

            latency=metric.get("latency"),
            packet_loss_percent=metric.get("packet_loss"),

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

        print(result)

        return result