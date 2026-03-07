from nexora_db.models.devices_model import Device
from nexora_db.configs.database import get_db
from datetime import datetime


class DeviceOperations:

    def __init__(self):
        self.session = next(get_db())

    def create_device(self, hostname, device_type, ip_address, mac_address, status="START", interval=None):
        try:
            device = self.session.query(Device).filter_by(mac_address=mac_address).first()

            if device:
                if device.status != status:
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
            raise e

        finally:
            self.session.close()

    def get_device_by_hostname(self, hostname):
        try:
            return self.session.query(Device).filter(Device.hostname == hostname).first()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_device_by_mac_address(self, mac_address):
        try:
            return self.session.query(Device).filter(Device.mac_address == mac_address).first()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_device_by_ip_address(self, ip_address):
        try:
            return self.session.query(Device).filter(Device.ip_address == ip_address).first()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_devices_by_status(self, status):
        try:
            return self.session.query(Device).filter(Device.status == status).all()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def update_last_seen(self, hostname):
        try:
            device = self.get_device_by_hostname(hostname)
            if device:
                device.last_seen = datetime.utcnow()
                self.session.commit()
                return device
            return None
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def check_device_status(self, hostname: str, status: str):
        try:
            if not hostname or not status:
                return False

            device = self.get_device_by_hostname(hostname)
            if not device:
                return False

            if device.status == status:
                self.update_last_seen(hostname)
                device.status = status
                self.session.commit()
                self.session.refresh(device)
                return True
            else:
                self.update_last_seen(hostname)

        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def delete_device(self, device_mac_address: str):
        try:
            device = self.get_device_by_mac_address(device_mac_address)
            if not device:
                return False

            self.session.delete(device)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def get_all_devices(self):
        try:
            return self.session.query(Device).all()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_device_by_ip(self, ip_address: str):
        try:
            return self.session.query(Device).filter(Device.ip_address == ip_address).first()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_device_by_mac(self, mac_address: str):
        try:
            return self.session.query(Device).filter(Device.mac_address == mac_address).first()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def update_device(self, mac_address: str, data: dict):
        try:
            if not mac_address or not data:
                return False

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
            raise e

        finally:
            self.session.close()