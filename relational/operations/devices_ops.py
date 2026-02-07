from relational.models.devices_model import Device
from relational.configs.database import sessionLocal, init_db
from datetime import datetime

class DeviceOperations:
    def __init__(self):
        self.session = sessionLocal()
        init_db()

    def create_device(self, hostname, device_type, ip_address, mac_address, status):

        try:
            device = self.session.query(Device).filter_by(mac_address=mac_address).first()

            if device:
                if device.status != status:
                    print(f"[STATUS CHANGE] {device.hostname}: {device.status} → {status}")
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
                    last_seen=datetime.utcnow()
                )
                self.session.add(device)
                print(f"[DEVICE CREATE] {hostname} | {status}")

            self.session.commit()
            return device

        except Exception as e:
            self.session.rollback()
            print("DEVICE OPS ERROR:", e)

        finally:
            self.session.close()


    def get_device_by_hostname(self, hostname: str):
        device = self.session.query(Device).filter(Device.hostname == hostname).first()
        if device:
            self.update_last_seen(hostname)
        return device



    def update_last_seen(self, hostname: str):
        device = self.get_device_by_hostname(hostname)
        if not device:
            return False

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


    def delete_device(self, device_hostname: str):
        device = self.get_device_by_hostname(device_hostname)
        if not device:
            return False

        self.session.delete(device)
        self.session.commit()
        return True