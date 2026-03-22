from nexora_db.models.alerts_model import Alerts
from nexora_db.operations.devices_ops import DeviceOperations
from nexora_db.configs.database import get_db
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
import logging

# Setup logger
logger = logging.getLogger('nexora_db.alerts')
logger.setLevel(logging.INFO)

class AlertOperations:

    def __init__(self):
        self.device_ops = DeviceOperations()


    def create_alert(self, alert_message, alert_level, device_id):
        session = next(get_db())
        try:
            logger.info(f"Creating alert: message={alert_message}, level={alert_level}, device_id={device_id}")

            alert = Alerts(
                alert_message=alert_message,
                alert_level=alert_level,
                device_id=device_id,
                alert_time=datetime.now(timezone.utc),  # Set timestamp explicitly for each alert (UTC)
            )

            session.add(alert)
            session.commit()
            session.refresh(alert)

            logger.info(f"Alert created successfully: id={alert.id}, alert_time={alert.alert_time}")
            return alert

        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            session.rollback()
            raise e

        finally:
            session.close()


    def get_all_alerts(self):
        session = next(get_db())
        try:
            # Use joinedload to eagerly load the device relationship
            return session.query(Alerts).options(joinedload(Alerts.device)).all()
        finally:
            session.close()


    def get_all_alerts_by_type(self, alert_level):
        session = next(get_db())
        try:
            # Use joinedload to eagerly load the device relationship
            alerts = session.query(Alerts).options(joinedload(Alerts.device)).filter(Alerts.alert_level == alert_level).all()
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


    def get_paginated_alerts(self, page: int = 1, page_size: int = 100):
        """
        Get paginated alerts sorted by alert_time DESC, then by id DESC (newest first).
        Returns dict with alerts list, total count, page info.
        """
        session = next(get_db())
        try:
            # Get total count
            total = session.query(Alerts).count()
            logger.info(f"[get_paginated_alerts] Total alerts in DB: {total}, page={page}, page_size={page_size}")

            if total == 0:
                return {
                    "alerts": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }

            # Get paginated alerts sorted by alert_time DESC (newest first)
            # Use id for secondary sort to handle potential null times
            # Use joinedload to eagerly load the device relationship
            from sqlalchemy import desc
            # Handle null alert_time by using coalesce
            query = session.query(Alerts).options(joinedload(Alerts.device)).order_by(desc(Alerts.alert_time), Alerts.id.desc())
            offset = (page - 1) * page_size
            paginated_alerts = query.offset(offset).limit(page_size).all()

            logger.info(f"[get_paginated_alerts] Retrieved {len(paginated_alerts)} alerts for page {page}")

            total_pages = (total + page_size - 1) // page_size  # Ceiling division

            return {
                "alerts": paginated_alerts,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

        except Exception as e:
            logger.error(f"[get_paginated_alerts] Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            session.rollback()
            raise e

        finally:
            session.close()


    def get_recent_alert(self, device_id: int, alert_message: str, minutes: int = 5):
        """
        Check if a similar alert exists for a device within the specified time window.
        Used for deduplication.
        Returns the existing alert if found, None otherwise.
        """
        session = next(get_db())
        try:
            from datetime import timedelta, timezone
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)

            existing = session.query(Alerts).filter(
                Alerts.device_id == device_id,
                Alerts.alert_message == alert_message,
                Alerts.alert_time >= time_threshold
            ).first()

            return existing

        except Exception as e:
            # On error, return None to allow alert creation
            print(f"[ALERT OPS][ERROR] {e}")
            return None

        finally:
            session.close()