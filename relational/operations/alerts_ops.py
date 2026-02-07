from relational.models.alerts_model import Alerts
from relational.configs.database import sessionLocal
from sqlalchemy.exc import SQLAlchemyError


class AlertOperations:
    def __init__(self):
        self.session = sessionLocal()
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
        return self.session.query(Alerts).all()


    def get_all_alerts_by_type(self, alert_level):
        return self.session.query(Alerts).filter(Alerts.alert_level == alert_level).all()


    def get_alerts_by_device(self, device_id: int):
        return self.session.query(Alerts).filter(Alerts.device_id == device_id).all()