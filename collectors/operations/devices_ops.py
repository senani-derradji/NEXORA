from models.devices_model import Device
from configs.database import sessionLocal
from datetime import datetime

class DeviceOperations:
    def __init__(self):
        self.session = sessionLocal()

    def create_device(self, hostname, device_type, ip_address, mac_address, status="START", interval=None):

        try:
            device = self.session.query(Device).filter_by(mac_address=mac_address).first()

            if device:
                if device.status != status:
                    print(f"[STATUS CHANGE] {device.hostname}: {device.status} -> {status}")
                    device.status = status
                    device.last_seen = datetime.utcnow()
                    self.session.commit()
                    self.session.refresh(device)
                    return device

            else:
                device = Device(
                    hostname=hostname,
                    device_type=device_type,
                    ip_address=ip_address,
                    mac_address=mac_address,
                    status=status,
                    interval=interval,
                    last_seen=datetime.utcnow()
                )

                self.session.add(device)
                self.session.commit()
                self.session.refresh(device)

            return device

        except Exception as e:
            self.session.rollback()
            print("DEVICE OPS ERROR:", e)

        finally:
            self.session.close()


    def get_device_by_hostname(self, hostname):
        return self.session.query(Device)\
                .filter(Device.hostname == hostname)\
                .first()

    def get_device_by_mac_address(self, mac_address):
        return self.session.query(Device).filter(Device.mac_address == mac_address).first()

    def get_device_by_ip_address(self, ip_address):
        return self.session.query(Device).filter(Device.ip_address == ip_address).first()

    def get_devices_by_status(self, status):
        return self.session.query(Device).filter(Device.status == status).all()

    def update_last_seen(self, hostname):
        device = self.get_device_by_hostname(hostname)
        if device:
            device.last_seen = datetime.utcnow()
            self.session.commit()
            return device
        device.last_seen = datetime.utcnow()
        self.session.commit()
        return True


    def check_device_status(self, hostname: str, status: str):
        if not hostname or not status:
            return False

        device = self.get_device_by_hostname(hostname)
        if not device:
            return False

        if device.status == status:
            self.update_last_seen(hostname) ; device.status = status ; self.session.commit() ; self.session.refresh(device)
            return True
        else:
            self.update_last_seen(hostname)


    def delete_device(self, device_mac_address: str):
        device = self.get_device_by_mac_address(device_mac_address)
        if not device:
            return False

        self.session.delete(device)
        self.session.commit()
        return True


    def get_all_devices(self):
        return self.session.query(Device).all()

    def get_device_by_ip(self, ip_address: str):
        return self.session.query(Device).filter(Device.ip_address == ip_address).first()

    def get_device_by_mac(self, mac_address: str):
        return self.session.query(Device).filter(Device.mac_address == mac_address).first()


    def update_device(self, mac_address: str, data: dict):
        if not mac_address or not data:
            return False

        try:
            device = self.session.query(Device).filter(Device.mac_address == mac_address).first()
            if not device:
                return False

            device.hostname    = data.get("hostname", device.hostname)
            device.device_type = data.get("device_type", device.device_type)
            device.ip_address  = data.get("ip_address", device.ip_address)

            self.session.commit()
            self.session.refresh(device)

            return device

        except Exception as e:
            self.session.rollback()
            return str(e)

        finally:
            self.session.close()
