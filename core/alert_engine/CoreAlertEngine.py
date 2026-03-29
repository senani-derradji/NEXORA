from core.configs.database import init ; init()
from nexora_db.operations.alerts_ops import AlertOperations
from nexora_db.operations.devices_ops import DeviceOperations
from datetime import datetime
import hashlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from core.utils.logger import setup_logger

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

try:
    from backend.api.routes.alert_broadcast import broadcast_alert_sync
except ImportError:
    try:
        from api.routes.alert_broadcast import broadcast_alert_sync
    except ImportError:
        broadcast_alert_sync = None

logger = setup_logger('core.alert_engine', level=20)


class AlertEngine:
    def __init__(self):
        self.alertOPS = AlertOperations()
        self.deviceOPS = DeviceOperations()
        self.dedup_window_minutes = 5

        self.alert_counts = {}
        self.rate_limit_window_seconds = 300
        self.max_alerts_per_type = 3

        self.traffic_warning_mbps = 1
        self.traffic_critical_mbps = 10

        logger.info("AlertEngine initialized with dedup window: 5 minutes, rate limit: 3 alerts/5min")

    def _should_create_alert(self, device_id: int, alert_message: str) -> bool:
        try:
            existing = self.alertOPS.get_recent_alert(
                device_id=device_id,
                alert_message=alert_message,
                minutes=self.dedup_window_minutes
            )

            if existing:
                logger.info(f"[ALERT DEDUP] Suppressed duplicate: '{alert_message}' for device {device_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"[ALERT DEDUP][ERROR] {e}")
            return True

    def _send_telegram(self, message: str, level: str = "WARNING"):
        import requests

        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

        prefix = {
            "CRITICAL": "🔴",
            "WARNING": "🟡",
            "INFO": "🔵"
        }.get(level, "⚪")

        text = f"{prefix} <b>[{level}]</b>\n{message}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })

        print(f"{prefix} [TELEGRAM/{level}] {message}")

    def cpu_alert(self, cpu, host: str = "unknown"):
        if cpu is None:
            return False
        if cpu > 95:
            self._send_telegram(
                f"[CPU CRITICAL] {host}: CPU usage at {cpu:.1f}% (threshold 95%)",
                level="CRITICAL"
            )
            return True
        if cpu > 50:
            self._send_telegram(
                f"[CPU WARNING] {host}: CPU usage at {cpu:.1f}% (threshold 50%)",
                level="WARNING"
            )
            return True
        return False

    def ram_alert(self, ram, host: str = "unknown"):
        if ram is None:
            return False
        if ram > 95:
            self._send_telegram(
                f"[RAM CRITICAL] {host}: RAM usage at {ram:.1f}% (threshold 95%)",
                level="CRITICAL"
            )
            return True
        if ram > 50:
            self._send_telegram(
                f"[RAM WARNING] {host}: RAM usage at {ram:.1f}% (threshold 50%)",
                level="WARNING"
            )
            return True
        return False

    def disk_alert(self, disk, host: str = "unknown"):
        if disk is None:
            return False
        if disk > 95:
            self._send_telegram(
                f"[DISK CRITICAL] {host}: Disk usage at {disk:.1f}% (threshold 95%)",
                level="CRITICAL"
            )
            return True
        if disk > 50:
            self._send_telegram(
                f"[DISK WARNING] {host}: Disk usage at {disk:.1f}% (threshold 50%)",
                level="WARNING"
            )
            return True
        return False

    def latency_alert(self, latency, host: str = "unknown"):
        if latency is None:
            return False
        if latency > 400:
            self._send_telegram(
                f"[LATENCY CRITICAL] {host}: Latency at {latency:.1f} ms (threshold 400 ms)",
                level="CRITICAL"
            )
            return True
        if latency > 50:
            self._send_telegram(
                f"[LATENCY WARNING] {host}: Latency at {latency:.1f} ms (threshold 50 ms)",
                level="WARNING"
            )
            return True
        return False

    def packet_loss_alert(self, packet_loss, host: str = "unknown"):
        if packet_loss is None:
            return False
        if packet_loss > 10:
            self._send_telegram(
                f"[PACKET LOSS CRITICAL] {host}: Packet loss at {packet_loss:.2f}% (threshold 10%)",
                level="CRITICAL"
            )
            return True
        if packet_loss > 1:
            self._send_telegram(
                f"[PACKET LOSS WARNING] {host}: Packet loss at {packet_loss:.2f}% (threshold 1%)",
                level="WARNING"
            )
            return True
        return False

    def in_bytes_alert(self, in_bytes, host: str = "unknown"):
        """
        Alert on inbound traffic.

        UNIT CONVERSION FIX:
        - SNMP OID_IF_IN_OCTETS returns bytes (octets), not bits
        - If input is bytes/sec: Mbps = bytes_per_sec * 8 / 1,000,000
        - If input is bytes (cumulative): needs delta calculation (not handled here)

        Default thresholds (in Mbps after conversion):
        - WARNING: 100 Mbps
        - CRITICAL: 500 Mbps
        """
        if in_bytes is None:
            return False

        try:
            in_mbps = (float(in_bytes) * 8) / 1_000_000
        except (ValueError, TypeError):
            logger.warning(f"[IN BYTES] Could not convert '{in_bytes}' to float")
            return False

        if in_mbps > self.traffic_critical_mbps:
            self._send_telegram(
                f"[IN TRAFFIC CRITICAL] {host}: Inbound traffic at {in_mbps:.2f} Mbps (threshold {self.traffic_critical_mbps} Mbps)",
                level="CRITICAL"
            )
            return True
        if in_mbps > self.traffic_warning_mbps:
            self._send_telegram(
                f"[IN TRAFFIC WARNING] {host}: Inbound traffic at {in_mbps:.2f} Mbps (threshold {self.traffic_warning_mbps} Mbps)",
                level="WARNING"
            )
            return True
        return False

    def out_bytes_alert(self, out_bytes, host: str = "unknown"):
        """
        Alert on outbound traffic.

        UNIT CONVERSION FIX:
        - SNMP OID_IF_OUT_OCTETS returns bytes (octets), not bits
        - If input is bytes/sec: Mbps = bytes_per_sec * 8 / 1,000,000

        Default thresholds (in Mbps after conversion):
        - WARNING: 100 Mbps
        - CRITICAL: 500 Mbps
        """
        if out_bytes is None:
            return False

        try:
            out_mbps = (float(out_bytes) * 8) / 1_000_000
        except (ValueError, TypeError):
            logger.warning(f"[OUT BYTES] Could not convert '{out_bytes}' to float")
            return False

        if out_mbps > self.traffic_critical_mbps:
            self._send_telegram(
                f"[OUT TRAFFIC CRITICAL] {host}: Outbound traffic at {out_mbps:.2f} Mbps (threshold {self.traffic_critical_mbps} Mbps)",
                level="CRITICAL"
            )
            return True
        if out_mbps > self.traffic_warning_mbps:
            self._send_telegram(
                f"[OUT TRAFFIC WARNING] {host}: Outbound traffic at {out_mbps:.2f} Mbps (threshold {self.traffic_warning_mbps} Mbps)",
                level="WARNING"
            )
            return True
        return False

    def in_packets_alert(self, in_packets, host: str = "unknown"):
        if in_packets is None:
            return False
        if in_packets > 900_000:
            self._send_telegram(
                f"[IN PACKETS CRITICAL] {host}: Inbound packet rate at {in_packets:,} pps (threshold 900k)",
                level="CRITICAL"
            )
            return True
        if in_packets > 500_000:
            self._send_telegram(
                f"[IN PACKETS WARNING] {host}: Inbound packet rate at {in_packets:,} pps (threshold 500k)",
                level="WARNING"
            )
            return True
        return False

    def out_packets_alert(self, out_packets, host: str = "unknown"):
        if out_packets is None:
            return False
        if out_packets > 900_000:
            self._send_telegram(
                f"[OUT PACKETS CRITICAL] {host}: Outbound packet rate at {out_packets:,} pps (threshold 900k)",
                level="CRITICAL"
            )
            return True
        if out_packets > 500_000:
            self._send_telegram(
                f"[OUT PACKETS WARNING] {host}: Outbound packet rate at {out_packets:,} pps (threshold 500k)",
                level="WARNING"
            )
            return True
        return False

    def in_errors_alert(self, in_errors, host: str = "unknown"):
        if in_errors is None:
            return False
        if in_errors > 2:
            self._send_telegram(
                f"[IN ERRORS CRITICAL] {host}: Inbound error rate at {in_errors:.2f}% (threshold 2%)",
                level="CRITICAL"
            )
            return True
        if in_errors > 0.5:
            self._send_telegram(
                f"[IN ERRORS WARNING] {host}: Inbound error rate at {in_errors:.2f}% (threshold 0.5%)",
                level="WARNING"
            )
            return True
        return False

    def out_errors_alert(self, out_errors, host: str = "unknown"):
        if out_errors is None:
            return False
        if out_errors > 2:
            self._send_telegram(
                f"[OUT ERRORS CRITICAL] {host}: Outbound error rate at {out_errors:.2f}% (threshold 2%)",
                level="CRITICAL"
            )
            return True
        if out_errors > 0.5:
            self._send_telegram(
                f"[OUT ERRORS WARNING] {host}: Outbound error rate at {out_errors:.2f}% (threshold 0.5%)",
                level="WARNING"
            )
            return True
        return False

    def Engine(self, status=None, hostname=None,
               cpu=None, ram=None, disk=None,
               latency=None, packet_loss_percent=None,
               in_bytes=None, out_bytes=None, in_packets=None, out_packets=None,
               in_errors=None, out_errors=None,
               device_id=None):

        alerts = {}

        if not status or not hostname:
            logger.warning(f"[ALERT ENGINE] Invalid input - status: {status}, hostname: {hostname}")
            return {"invalid_input": True}

        if not device_id:
            device = self.deviceOPS.get_device_by_hostname(hostname)
            if not device:
                logger.warning(f"[ALERT ENGINE] Device not found by hostname: {hostname}, attempting to find by other means")
                # Return a flag indicating device needs to be created first
                return {"device_missing": True, "hostname": hostname}
            dev_id = device.id
        else:
            dev_id = device_id

        if not dev_id:
            logger.error(f"[ALERT ENGINE] Cannot proceed - no valid device_id for hostname: {hostname}")
            return {"no_device_id": True, "hostname": hostname}

        logger.debug(f"[ALERT ENGINE] Processing alerts for device_id={dev_id}, hostname={hostname}, status={status}")
        status = status.lower()

        if status == "down":
            msg = f"Device {hostname} is DOWN"
            if self._should_create_alert(dev_id, msg):
                try:
                    self.alertOPS.create_alert(
                        alert_level="high",
                        alert_message=msg,
                        device_id=dev_id
                    )
                    logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                    # Broadcast to WebSocket clients - include hostname for display
                    if broadcast_alert_sync:
                        broadcast_alert_sync({
                            "id": None,  # Will be assigned by DB
                            "message": msg,
                            "severity": "HIGH",
                            "device_id": dev_id,
                            "device_hostname": hostname  # Add hostname for WebSocket display
                        })
                except Exception as e:
                    logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            return {"down": True}

        if status == "up":

            alerts["cpu"] = self.cpu_alert(cpu, hostname)
            alerts["ram"] = self.ram_alert(ram, hostname)
            alerts["disk"] = self.disk_alert(disk, hostname)
            alerts["latency"] = self.latency_alert(latency, hostname)
            alerts["packet_loss"] = self.packet_loss_alert(packet_loss_percent, hostname)
            alerts["in_bytes"] = self.in_bytes_alert(in_bytes, hostname)
            alerts["out_bytes"] = self.out_bytes_alert(out_bytes, hostname)
            alerts["in_packets"] = self.in_packets_alert(in_packets, hostname)
            alerts["out_packets"] = self.out_packets_alert(out_packets, hostname)
            alerts["in_errors"] = self.in_errors_alert(in_errors, hostname)
            alerts["out_errors"] = self.out_errors_alert(out_errors, hostname)


            if alerts["cpu"] or alerts["ram"]:
                msg = f"High load: CPU={cpu}%, RAM={ram}%"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["disk"]:
                msg = f"High disk usage: Disk={disk}%"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="low",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "LOW",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["latency"]:
                msg = f"High latency: {latency} ms"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["packet_loss"]:
                msg = f"Packet loss detected: {packet_loss_percent}%"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["in_bytes"] or alerts["out_bytes"]:
                in_mbps = (float(in_bytes) * 8) / 1_000_000 if in_bytes else 0
                out_mbps = (float(out_bytes) * 8) / 1_000_000 if out_bytes else 0
                msg = f"High traffic: in={in_mbps:.2f} Mbps / out={out_mbps:.2f} Mbps"

                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["in_packets"] or alerts["out_packets"]:
                msg = f"High packets: in={in_packets} / out={out_packets}"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")

            if alerts["in_errors"] or alerts["out_errors"]:
                msg = f"Network errors: in={in_errors} / out={out_errors}"
                if self._should_create_alert(dev_id, msg):
                    try:
                        self.alertOPS.create_alert(
                            alert_level="mid",
                            alert_message=msg,
                            device_id=dev_id
                        )
                        logger.info(f" ALERT CREATED: {msg} for device_id={dev_id}")
                        # Broadcast to WebSocket clients - include hostname for display
                        if broadcast_alert_sync:
                            broadcast_alert_sync({
                                "id": None,
                                "message": msg,
                                "severity": "MID",
                                "device_id": dev_id,
                                "device_hostname": hostname  # Add hostname for WebSocket display
                            })
                    except Exception as e:
                        logger.error(f"❌ FAILED TO CREATE ALERT: {msg}, error: {e}")


        return alerts