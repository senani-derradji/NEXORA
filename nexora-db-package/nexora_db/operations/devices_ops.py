from nexora_db.models.devices_model import Device
from nexora_db.configs.database import get_db
from datetime import datetime


class DeviceOperations:
    
    def create_device(self, hostname, device_type, ip_address, mac_address, status="START", interval=None):
        session = next(get_db())
        try:
            device = session.query(Device).filter(Device.ip_address == ip_address).first()

            if device:
                if device.status != status:
                    device.status = status
                    device.last_seen = datetime.utcnow()
                    session.commit()
                    session.refresh(device)
                return device

            device = Device(
                hostname=hostname,
                device_type=device_type,
                ip_address=ip_address,
                mac_address=mac_address,
                status=status,
                interval=interval,
                last_seen=datetime.utcnow()
            )

            session.add(device)
            session.commit()
            session.refresh(device)

            return device

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def get_device_by_hostname(self, hostname):
        session = next(get_db())
        try:
            return session.query(Device).filter(Device.hostname == hostname).first()
        finally:
            session.close()


    def get_device_by_mac(self, mac_address):
        session = next(get_db())
        try:
            return session.query(Device).filter(Device.mac_address == mac_address).first()
        finally:
            session.close()


    def get_device_by_ip(self, ip_address):
        session = next(get_db())
        try:
            return session.query(Device).filter(Device.ip_address == ip_address).first()
        finally:
            session.close()


    def get_devices_by_status(self, status):
        session = next(get_db())
        try:
            return session.query(Device).filter(Device.status == status).all()
        finally:
            session.close()


    def update_last_seen(self, ip_address):
        session = next(get_db())
        try:
            device = session.query(Device).filter(Device.ip_address == ip_address).first()
            if not device:
                return None

            device.last_seen = datetime.utcnow()
            session.commit()
            session.refresh(device)

            return device

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def update_device_status(self, ip_address, status, last_seen=None):
        session = next(get_db())
        try:
            device = session.query(Device).filter(Device.ip_address == ip_address).first()

            if not device:
                return None

            device.status = status
            device.last_seen = last_seen or datetime.utcnow()

            session.commit()
            session.refresh(device)

            return device

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def update_device(self, mac_address, data: dict):
        session = next(get_db())
        try:
            device = session.query(Device).filter(Device.mac_address == mac_address).first()
            if not device:
                return None

            device.hostname = data.get("hostname", device.hostname)
            device.device_type = data.get("device_type", device.device_type)
            device.ip_address = data.get("ip_address", device.ip_address)

            session.commit()
            session.refresh(device)

            return device

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def delete_device(self, mac_address):
        session = next(get_db())
        try:
            device = session.query(Device).filter(Device.mac_address == mac_address).first()
            if not device:
                return False

            session.delete(device)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def get_all_devices(self):
        session = next(get_db())
        try:
            return session.query(Device).all()
        finally:
            session.close()