from ..models.alerts_model import Alerts
from ..configs.database import get_db
from ..schemas.alerts_validator import AlertValidate


class AlertOperations:
    def __init__(self, db = get_db):
        self.session = db

    def create_alert(self, alert: AlertValidate):
        alert = Alerts(
                    alert_level=alert.alert_level,
                    alert_message=alert.alert_message,
                    device_id=alert.device_id
                    )
        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)
        return alert

    def get_all_alerts(self):
        return self.session.query(Alerts).all()

    def get_all_alerts_by_type(self, alert_level: AlertValidate):
        return self.session.query(Alerts).filter(Alerts.alert_level == alert_level).all()

    def get_alerts_by_device(self, device_id: int):
        return self.session.query(Alerts).filter(Alerts.device_id == device_id).all()