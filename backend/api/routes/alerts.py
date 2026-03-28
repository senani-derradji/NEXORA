from fastapi import APIRouter, Depends, HTTPException, Query
from nexora_db.models.alerts_model import Alerts
from nexora_db.configs.database import get_db
from security.jwt import get_current_user
from config import init
from datetime import datetime
from utils.logger import setup_logger
from sqlalchemy.orm import joinedload

logger = setup_logger('backend.alerts', level=20)

init(url_env="DATABASE_URL")

router = APIRouter()

DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500
REALTIME_PAGE_SIZE = 10

def _serialize_alert(alert):
    def format_time(dt):
        if dt is None:
            return None
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return str(dt)

    device_hostname = None
    device_ip = None
    device_mac = None
    try:
        from sqlalchemy import inspect as sqla_inspect
        if sqla_inspect(alert).detached:
            pass
        elif hasattr(alert, 'device') and alert.device is not None:
            device_hostname = alert.device.hostname
            device_ip = getattr(alert.device, 'ip_address', None) or getattr(alert.device, 'ip', None)
            device_mac = getattr(alert.device, 'mac_address', None) or getattr(alert.device, 'mac', None)
    except Exception:
        pass

    return {
        "id": alert.id,
        "message": alert.alert_message,
        "description": alert.alert_message,
        "alert_message": alert.alert_message,
        "severity": str(alert.alert_level).upper() if alert.alert_level else 'INFO',
        "alert_level": str(alert.alert_level).upper() if alert.alert_level else 'INFO',
        "timestamp": format_time(alert.alert_time),
        "created_at": format_time(alert.alert_time),
        "alert_time": format_time(alert.alert_time),
        "device_id": alert.device_id,
        "device_hostname": device_hostname,
        "device_ip": device_ip,
        "device_mac": device_mac
    }

def _require_admin_or_viewer():
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.get("/")
def all_alerts(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE, description="Number of alerts per page"),
    after_id: int = Query(None, description="Return only alerts with ID greater than this value"),
    after_timestamp: str = Query(None, description="Return only alerts created after this timestamp"),
    limit: int = Query(None, ge=1, le=MAX_PAGE_SIZE, description="Limit number of results (alternative to page_size)"),
    user: dict = Depends(_require_admin_or_viewer())
):
    logger.info(f"Fetching alerts - page: {page}, page_size: {page_size}, after_id: {after_id}, after_timestamp: {after_timestamp}, user: {user.get('email', 'unknown')}")

    session = next(get_db())
    try:
        query = session.query(Alerts).options(joinedload(Alerts.device))

        if after_id is not None:
            query = query.filter(Alerts.id > after_id)

        if after_timestamp is not None:
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(after_timestamp.replace('Z', '+00:00'))
                query = query.filter(Alerts.alert_time > ts)
            except Exception as e:
                logger.warning(f"Invalid after_timestamp format: {after_timestamp}, error: {e}")

        total = query.count()
        logger.info(f"[alerts API] Total alerts matching filters: {total}")

        if total == 0:
            logger.info("No alerts found matching filters")
            return {
                "alerts": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "message": "No alerts found"
            }

        effective_page_size = limit if limit else page_size

        query = query.order_by(Alerts.alert_time.desc(), Alerts.id.desc())

        returned_count = 0
        if after_id is not None:
            paginated_alerts = query.limit(effective_page_size).all()
            returned_count = len(paginated_alerts)
            logger.info(f"[alerts API] Incremental mode: Retrieved {returned_count} new alerts after ID {after_id}")
        elif after_timestamp is not None:
            paginated_alerts = query.limit(effective_page_size).all()
            returned_count = len(paginated_alerts)
            logger.info(f"[alerts API] Timestamp mode: Retrieved {returned_count} alerts after {after_timestamp}")
        else:
            realtime_count = min(effective_page_size, MAX_PAGE_SIZE)
            if effective_page_size > MAX_PAGE_SIZE:
                logger.info(f"[alerts API] Large page size requested ({effective_page_size}), capped at {MAX_PAGE_SIZE}")
            paginated_alerts = query.limit(realtime_count).all()
            returned_count = len(paginated_alerts)
            logger.info(f"[alerts API] Pagination mode: Retrieved {returned_count} alerts (page {page})")

        logger.info(f"[alerts API] Retrieved {len(paginated_alerts)} alerts")

        # Serialize alerts
        serialized_alerts = [_serialize_alert(a) for a in paginated_alerts]

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        logger.info(f"Returning {len(serialized_alerts)} alerts (total: {total})")

        return {
            "alerts": serialized_alerts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch alerts: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {
            "alerts": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "message": f"Error: {str(e)}"
        }
    finally:
        session.close()


@router.get("/stats")
def get_alert_stats(user: dict = Depends(_require_admin_or_viewer())):
    logger.info(f"Fetching alert stats, user: {user.get('email', 'unknown')}")

    session = next(get_db())
    try:
        alerts = session.query(Alerts).all()
        logger.info(f"[stats] Retrieved {len(alerts)} alerts from DB")
    except Exception as e:
        logger.error(f"[stats] Error getting alerts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        alerts = []
    finally:
        session.close()

    logger.info(f"Found {len(alerts)} alerts for stats")

    if not alerts:
        return {
            "critical": 0,
            "warnings": 0,
            "info": 0,
            "total": 0
        }

    critical = 0
    warnings = 0
    info = 0

    for alert in alerts:
        level = str(alert.alert_level).upper() if alert.alert_level else 'INFO'
        if level in ['CRITICAL', 'HIGH']:
            critical += 1
        elif level in ['WARNING', 'MID']:
            warnings += 1
        else:
            info += 1

    logger.info(f"Stats: critical={critical}, warnings={warnings}, info={info}, total={len(alerts)}")

    return {
        "critical": critical,
        "warnings": warnings,
        "info": info,
        "total": len(alerts)
    }


@router.get("/{device_hostname}")
def get_alerts(device_hostname: str, user: dict = Depends(_require_admin_or_viewer())):
    session = next(get_db())
    try:
        from nexora_db.operations.devices_ops import DeviceOperations
        device_ops = DeviceOperations()
        device = device_ops.get_device_by_hostname(device_hostname)

        if not device:
            return {"alerts": [], "message": f"No alerts found for {device_hostname}"}

        alerts = session.query(Alerts).filter(Alerts.device_id == device.id).all()

        if not alerts:
            return {"alerts": [], "message": f"No alerts found for {device_hostname}"}

        serialized_alerts = [_serialize_alert(a) for a in alerts]
        return {"alerts": serialized_alerts}
    except Exception as e:
        logger.error(f"Error getting alerts for device {device_hostname}: {e}")
        return {"alerts": [], "message": f"Error: {str(e)}"}
    finally:
        session.close()


@router.get("/realtime")
def get_realtime_alerts(
    page: int = Query(1, ge=1, description="Page number (1-based) for real-time updates"),
    user: dict = Depends(_require_admin_or_viewer())
):
    logger.info(f"[Realtime Alerts] Fetching page {page}, user: {user.get('email', 'unknown')}")

    page_size = REALTIME_PAGE_SIZE

    session = next(get_db())
    try:
        total = session.query(Alerts).count()
        logger.info(f"[Realtime Alerts] Total alerts in DB: {total}")

        if total == 0:
            return {
                "alerts": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "message": "No alerts found"
            }

        query = session.query(Alerts).options(joinedload(Alerts.device)).order_by(Alerts.alert_time.desc(), Alerts.id.desc())
        offset = (page - 1) * page_size
        paginated_alerts = query.offset(offset).limit(page_size).all()

        logger.info(f"[Realtime Alerts] Retrieved {len(paginated_alerts)} alerts for page {page}")

        # Serialize alerts
        serialized_alerts = [_serialize_alert(a) for a in paginated_alerts]

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return {
            "alerts": serialized_alerts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch realtime alerts: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {
            "alerts": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "message": f"Error: {str(e)}"
        }
    finally:
        session.close()


@router.delete("/{device_hostname}")
def delete_alert(device_hostname: str):
    session = next(get_db())
    try:
        from nexora_db.operations.devices_ops import DeviceOperations
        device_ops = DeviceOperations()
        device = device_ops.get_device_by_hostname(device_hostname)

        if not device:
            return {"success": False, "message": f"Alert doesn't exist for {device_hostname}"}

        deleted = session.query(Alerts).filter(Alerts.device_id == device.id).delete()
        session.commit()

        return {"success": True, "message": f"Alerts deleted successfully for {device_hostname}"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        session.close()


@router.get("/latest")
def get_latest_alerts(
    limit: int = Query(50, ge=1, le=100, description="Number of latest alerts to return"),
    user: dict = Depends(_require_admin_or_viewer())
):
    logger.info(f"[Latest Alerts] Fetching {limit} latest alerts, user: {user.get('email', 'unknown')}")

    session = next(get_db())
    try:
        query = session.query(Alerts).options(
            joinedload(Alerts.device)
        ).order_by(
            Alerts.alert_time.desc(),
            Alerts.id.desc()
        ).limit(limit)

        paginated_alerts = query.all()
        logger.info(f"[Latest Alerts] Retrieved {len(paginated_alerts)} alerts")

        # Serialize alerts
        serialized_alerts = [_serialize_alert(a) for a in paginated_alerts]

        return {
            "alerts": serialized_alerts,
            "total": len(serialized_alerts),
            "limit": limit
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch latest alerts: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {
            "alerts": [],
            "total": 0,
            "limit": limit,
            "message": f"Error: {str(e)}"
        }
    finally:
        session.close()
