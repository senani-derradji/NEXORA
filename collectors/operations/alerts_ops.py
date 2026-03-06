from models.alerts_model import Alerts
from config.db_config.database import sessionLocal
from sqlalchemy.exc import SQLAlchemyError
from operations.devices_ops import DeviceOperations


class AlertOperations:

    def __init__(self):
        self.session = sessionLocal()
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
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"[AlertOPS] DB ERROR: {e}")


    def get_all_alerts(self):
        length_of_alerts = len(self.session.query(Alerts).all())
        if not length_of_alerts:
            return False
        return length_of_alerts


    def get_all_alerts_by_type(self, alert_level):
        alerts_by_type = self.session.query(Alerts).filter(Alerts.alert_level == alert_level).all()
        if not alerts_by_type:
            return False
        return alerts_by_type


    def get_alerts_by_device_hostname(self, hostname: int):
        alerts = self.device_ops.get_device_by_hostname(hostname).alerts_device
        if not alerts:
            return False
        return alerts


    def delete_alert(self, alert_id: int):
        alert = self.session.query(Alerts).filter(Alerts.id == alert_id).first()
        if not alert:
            return False
        self.session.delete(alert)
        self.session.commit()
        return True

    def get_all_alerts(self):
        return self.session.query(Alerts).all()

    def delete_alerts_by_device_hostname(self, hostname: str):
        device = self.device_ops.get_device_by_hostname(hostname)
        if not device:
            return False
        self.session.query(Alerts).filter(Alerts.device_id == device.id).delete()
        self.session.commit()
        return True