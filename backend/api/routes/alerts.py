from fastapi import APIRouter, Depends, HTTPException, Query
from nexora_db.models.alerts_model import Alerts
from nexora_db.configs.database import get_db
from security.jwt import get_current_user
from config import init
from datetime import datetime
from utils.logger import setup_logger
from sqlalchemy.orm import joinedload

# Setup logger
logger = setup_logger('backend.alerts', level=20)

init(url_env="DATABASE_URL")

router = APIRouter()

DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500
REALTIME_PAGE_SIZE = 10  # For real-time dashboard updates

def _serialize_alert(alert):
    """Serialize alert to JSON with proper field names for frontend"""
    # Handle both timezone-aware and naive datetime
    def format_time(dt):
        if dt is None:
            return None
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return str(dt)

    # Get device hostname from relationship if available
    # Use safe check to avoid DetachedInstanceError
    device_hostname = None
    try:
        # Check if the object is attached to a session
        from sqlalchemy import inspect as sqla_inspect
        if sqla_inspect(alert).detached:
            # Object is detached, can't access relationship
            pass
        elif hasattr(alert, 'device') and alert.device is not None:
            device_hostname = alert.device.hostname
    except Exception:
        # If any error occurs, just skip the device hostname
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
        "device_hostname": device_hostname
    }

def _require_admin_or_viewer():
    """Allow both admin and viewer roles"""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.get("/")
def all_alerts(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Number of alerts per page"),
    user: dict = Depends(_require_admin_or_viewer())
):
    logger.info(f"Fetching alerts - page: {page}, page_size: {page_size}, user: {user.get('email', 'unknown')}")

    # Use direct SQLAlchemy session queries
    session = next(get_db())
    try:
        # Get total count
        total = session.query(Alerts).count()
        logger.info(f"[alerts API] Total alerts in DB: {total}")

        if total == 0:
            logger.info("No alerts found in database")
            return {
                "alerts": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "message": "No alerts found"
            }

        # Get paginated alerts sorted by alert_time DESC (newest first)
        # Use joinedload to eagerly load device relationship
        query = session.query(Alerts).options(joinedload(Alerts.device)).order_by(Alerts.alert_time.desc(), Alerts.id.desc())
        offset = (page - 1) * page_size
        paginated_alerts = query.offset(offset).limit(page_size).all()

        logger.info(f"[alerts API] Retrieved {len(paginated_alerts)} alerts for page {page}")

        # Serialize alerts
        serialized_alerts = [_serialize_alert(a) for a in paginated_alerts]

        print(f"""
              ___________________________________________________
              [ALERTS API]
              Total: {total}
              Page: {page}
              Page size: {page_size}
              Total pages: {(total + page_size - 1) // page_size}
              ___________________________________________________
              """)

        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        logger.info(f"Total alerts: {total}, Page: {page}, PageSize: {page_size}")
        logger.info(f"Returning {len(serialized_alerts)} alerts (page {page}), total: {total}")

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
    """Get alert statistics"""
    logger.info(f"Fetching alert stats, user: {user.get('email', 'unknown')}")

    # Use direct SQLAlchemy session query
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


# NOTE: /{device_hostname} route moved to the END to avoid route conflict with /stats
# The /stats route must be registered before /{device_hostname} to work correctly
@router.get("/{device_hostname}")
def get_alerts(device_hostname: str, user: dict = Depends(_require_admin_or_viewer())):
    session = next(get_db())
    try:
        # Get device first
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
    """
    Get alerts for real-time dashboard display.
    Returns 10 alerts per page, sorted by newest first.
    Designed to be polled every 1 second for live updates.
    """
    logger.info(f"[Realtime Alerts] Fetching page {page}, user: {user.get('email', 'unknown')}")

    page_size = REALTIME_PAGE_SIZE  # 10 alerts per page

    session = next(get_db())
    try:
        # Get total count
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

        # Get paginated alerts sorted by alert_time DESC (newest first)
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
