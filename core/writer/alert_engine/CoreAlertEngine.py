from relational.operations.alerts_ops import AlertOperations
from relational.operations.devices_ops import DeviceOperations
from relational.configs.database import sessionLocal
from relational.models.devices_model import Device


class AlertEngine:
    def __init__(self):
        self.alertOPS = AlertOperations()
        self.deviceOPS = DeviceOperations()
        self.session = sessionLocal()


    def cpu_alert(self, cpu):
        print("cpu alert: ", cpu)
        if cpu is None:
            return False
        return cpu > 70

    def ram_alert(self, ram):
        print("ram alert: ", ram)
        if ram is None:
            return False
        return ram > 70

    def disk_alert(self, disk):
        print("disk alert: ", disk)
        if disk is None:
            return False
        return disk > 70

    def latency_alert(self, latency):
        print("latency alert: ", latency)
        if latency is None:
            return False
        return latency > 70

    def packet_loss_alert(self, packet_loss_percent):
        print("packet loss alert: ", packet_loss_percent)
        if packet_loss_percent is None:
            return False
        return packet_loss_percent > 70

    def in_bytes_alert(self, in_bytes):
        print("in bytes alert: ", in_bytes)
        if in_bytes is None:
            return False
        return in_bytes > 70

    def out_bytes_alert(self, out_bytes):
        print("out bytes alert: ", out_bytes)
        if out_bytes is None:
            return False
        return out_bytes > 70

    def in_packets_alert(self, in_packets):
        print("in packets alert: ", in_packets)
        if in_packets is None:
            return False
        return in_packets > 70

    def out_packets_alert(self, out_packets):
        print("out packets alert: ", out_packets)
        if out_packets is None:
            return False
        return out_packets > 70

    def in_errors_alert(self, in_errors):
        print("in errors alert: ", in_errors)
        if in_errors is None:
            return False
        return in_errors > 70

    def out_errors_alert(self, out_errors):
        print("out errors alert: ", out_errors)
        if out_errors is None:
            return False
        return out_errors > 70


    def Engine(self, status=None, hostname=None,
               cpu=None, ram=None, disk=None,
               latency=None, packet_loss_percent=None,
               in_bytes=None, out_bytes=None, in_packets=None, out_packets=None,
               in_errors=None, out_errors=None,
               device_id=None):

        if not device_id and hostname:
            device = self.session.query(Device).filter(Device.hostname == hostname).first()
            if not device:
                print(f"[AlertEngine] Device not found: {hostname}")
                return
            dev_id = device.id
        else:
            dev_id = device_id

        if not status or not hostname:
            return

        status = status.lower()

        if status == "down":
            self.alertOPS.create_alert(
                alert_level="high",
                alert_message=f"Device {hostname} is DOWN",
                device_id=dev_id
            )
            return

        if status == "up":

            if self.cpu_alert(cpu) or self.ram_alert(ram):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High load: CPU={cpu}%, RAM={ram}%",
                    device_id=dev_id
                )

            if self.disk_alert(disk):
                self.alertOPS.create_alert(
                    alert_level="low",
                    alert_message=f"High disk usage: Disk={disk}%",
                    device_id=dev_id
                )

            if self.latency_alert(latency):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High latency: {latency} ms",
                    device_id=dev_id
                )

            if self.packet_loss_alert(packet_loss_percent):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"Packet loss detected: {packet_loss_percent}%",
                    device_id=dev_id
                )

            if self.in_bytes_alert(in_bytes) or self.out_bytes_alert(out_bytes):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High in_bytes: {in_bytes} / High out_bytes: {out_bytes}",
                    device_id=dev_id
                )

            if self.in_packets_alert(in_packets) or self.out_packets_alert(out_packets):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High in_packets: {in_packets} / High out_packets: {out_packets}",
                    device_id=dev_id
                )

            if self.in_errors_alert(in_errors) or self.out_errors_alert(out_errors):
                self.alertOPS.create_alert(
                    alert_level="mid",
                    alert_message=f"High in_errors: {in_errors} / High out_errors: {out_errors}",
                    device_id=dev_id
                )
