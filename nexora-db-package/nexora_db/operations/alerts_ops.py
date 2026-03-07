from nexora_db.models.alerts_model import Alerts
from nexora_db.operations.devices_ops import DeviceOperations
from nexora_db.configs.database import get_db


class AlertOperations:

    def __init__(self):
        self.session = next(get_db())
        self.device_ops = DeviceOperations()

    def create_alert(self, alert_message, alert_level, device_id):
        try:
            alert = Alerts(
                alert_message=alert_message,
                alert_level=alert_level,
                device_id=device_id,
            )
            self.session.add(alert)
            self.session.commit()
            return alert
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def get_all_alerts(self):
        try:
            return self.session.query(Alerts).all()
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_all_alerts_by_type(self, alert_level):
        try:
            alerts_by_type = self.session.query(Alerts).filter(Alerts.alert_level == alert_level).all()
            if not alerts_by_type:
                return False
            return alerts_by_type
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def get_alerts_by_device_hostname(self, hostname: str):
        try:
            alerts = self.device_ops.get_device_by_hostname(hostname).alerts_device
            if not alerts:
                return False
            return alerts
        except Exception as e:
            raise e
        finally:
            self.session.close()

    def delete_alert(self, alert_id: int):
        try:
            alert = self.session.query(Alerts).filter(Alerts.id == alert_id).first()
            if not alert:
                return False
            self.session.delete(alert)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def delete_alerts_by_device_hostname(self, hostname: str):
        try:
            device = self.device_ops.get_device_by_hostname(hostname)
            if not device:
                return False
            self.session.query(Alerts).filter(Alerts.device_id == device.id).delete()
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()