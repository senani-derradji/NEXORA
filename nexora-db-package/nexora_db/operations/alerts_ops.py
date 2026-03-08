from nexora_db.models.alerts_model import Alerts
from nexora_db.operations.devices_ops import DeviceOperations
from nexora_db.configs.database import get_db


class AlertOperations:

    def __init__(self):
        self.device_ops = DeviceOperations()


    def create_alert(self, alert_message, alert_level, device_id):
        session = next(get_db())
        try:
            alert = Alerts(
                alert_message=alert_message,
                alert_level=alert_level,
                device_id=device_id,
            )

            session.add(alert)
            session.commit()
            session.refresh(alert)

            return alert

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def get_all_alerts(self):
        session = next(get_db())
        try:
            return session.query(Alerts).all()
        finally:
            session.close()


    def get_all_alerts_by_type(self, alert_level):
        session = next(get_db())
        try:
            alerts = session.query(Alerts).filter(Alerts.alert_level == alert_level).all()
            return alerts if alerts else False
        finally:
            session.close()


    def get_alerts_by_device_hostname(self, hostname: str):
        session = next(get_db())
        try:
            device = self.device_ops.get_device_by_hostname(hostname)

            if not device:
                return False

            alerts = session.query(Alerts).filter(Alerts.device_id == device.id).all()

            return alerts if alerts else False

        finally:
            session.close()


    def delete_alert(self, alert_id: int):
        session = next(get_db())
        try:
            alert = session.query(Alerts).filter(Alerts.id == alert_id).first()

            if not alert:
                return False

            session.delete(alert)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()


    def delete_alerts_by_device_hostname(self, hostname: str):
        session = next(get_db())
        try:
            device = self.device_ops.get_device_by_hostname(hostname)

            if not device:
                return False

            session.query(Alerts).filter(Alerts.device_id == device.id).delete()
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()