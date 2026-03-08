from core.configs.database import init ; init()
from nexora_db.operations.alerts_ops import AlertOperations
from nexora_db.operations.devices_ops import DeviceOperations
from nexora_db.configs.database import get_db
from nexora_db.models.devices_model import Device


class AlertEngine:
    def __init__(self):
        self.alertOPS = AlertOperations()
        self.deviceOPS = DeviceOperations()
        self.session = next(get_db())

    def _send_telegram(self, message: str, level: str = "WARNING"):
        """
        Example real implementation:
            import requests
            BOT_TOKEN = "your_bot_token"
            CHAT_ID   = "your_chat_id"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": f"[{level}] {message}"})
        """

        prefix = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(level, "⚪")
        print(f"{prefix} [TELEGRAM/{level}] {message}")

    def cpu_alert(self, cpu, host: str = "unknown"):
        if cpu is None:
            return False
        if cpu > 90:
            self._send_telegram(
                f"[CPU CRITICAL] {host}: CPU usage at {cpu:.1f}% (threshold 90%)",
                level="CRITICAL"
            )
            return True
        if cpu > 85:
            self._send_telegram(
                f"[CPU WARNING] {host}: CPU usage at {cpu:.1f}% (threshold 85%)",
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
        if ram > 80:
            self._send_telegram(
                f"[RAM WARNING] {host}: RAM usage at {ram:.1f}% (threshold 80%)",
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
        if disk > 80:
            self._send_telegram(
                f"[DISK WARNING] {host}: Disk usage at {disk:.1f}% (threshold 80%)",
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
        if latency > 150:
            self._send_telegram(
                f"[LATENCY WARNING] {host}: Latency at {latency:.1f} ms (threshold 150 ms)",
                level="WARNING"
            )
            return True
        return False

    def packet_loss_alert(self, packet_loss, host: str = "unknown"):
        if packet_loss is None:
            return False
        if packet_loss > 5:
            self._send_telegram(
                f"[PACKET LOSS CRITICAL] {host}: Packet loss at {packet_loss:.2f}% (threshold 5%)",
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
        if in_bytes is None:
            return False
        if in_bytes > 950:
            self._send_telegram(
                f"[IN BYTES CRITICAL] {host}: Inbound traffic at {in_bytes} Mbps (threshold 950 Mbps)",
                level="CRITICAL"
            )
            return True
        if in_bytes > 800:
            self._send_telegram(
                f"[IN BYTES WARNING] {host}: Inbound traffic at {in_bytes} Mbps (threshold 800 Mbps)",
                level="WARNING"
            )
            return True
        return False

    def out_bytes_alert(self, out_bytes, host: str = "unknown"):
        if out_bytes is None:
            return False
        if out_bytes > 950:
            self._send_telegram(
                f"[OUT BYTES CRITICAL] {host}: Outbound traffic at {out_bytes} Mbps (threshold 950 Mbps)",
                level="CRITICAL"
            )
            return True
        if out_bytes > 800:
            self._send_telegram(
                f"[OUT BYTES WARNING] {host}: Outbound traffic at {out_bytes} Mbps (threshold 800 Mbps)",
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
            return {"invalid_input": True}

        if not device_id:
            device = self.session.query(Device).filter(Device.hostname == hostname).first()
            if not device:
                return {"device_missing": True}
            dev_id = device.id
        else:
            dev_id = device_id

        status = status.lower()

        if status == "down":
            self.alertOPS.create_alert(
                alert_level="high",
                alert_message=f"Device {hostname} is DOWN",
                device_id=dev_id
            )
            
            return {"down": True}

        if status == "up":

            alerts["cpu"] = self.cpu_alert(cpu)
            alerts["ram"] = self.ram_alert(ram)
            alerts["disk"] = self.disk_alert(disk)
            alerts["latency"] = self.latency_alert(latency)
            alerts["packet_loss"] = self.packet_loss_alert(packet_loss_percent)
            alerts["in_bytes"] = self.in_bytes_alert(in_bytes)
            alerts["out_bytes"] = self.out_bytes_alert(out_bytes)
            alerts["in_packets"] = self.in_packets_alert(in_packets)
            alerts["out_packets"] = self.out_packets_alert(out_packets)
            alerts["in_errors"] = self.in_errors_alert(in_errors)
            alerts["out_errors"] = self.out_errors_alert(out_errors)


            if alerts["cpu"] or alerts["ram"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High load: CPU={cpu}%, RAM={ram}%",
                    device_id=dev_id
                )

            if alerts["disk"]:
                self.alertOPS.create_alert(
                    alert_level="low",
                    alert_message=f"High disk usage: Disk={disk}%",
                    device_id=dev_id
                )

            if alerts["latency"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High latency: {latency} ms",
                    device_id=dev_id
                )

            if alerts["packet_loss"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"Packet loss detected: {packet_loss_percent}%",
                    device_id=dev_id
                )

            if alerts["in_bytes"] or alerts["out_bytes"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High traffic: in={in_bytes} / out={out_bytes}",
                    device_id=dev_id
                )

            if alerts["in_packets"] or alerts["out_packets"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High packets: in={in_packets} / out={out_packets}",
                    device_id=dev_id
                )

            if alerts["in_errors"] or alerts["out_errors"]:
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"Network errors: in={in_errors} / out={out_errors}",
                    device_id=dev_id
                )


        return alerts