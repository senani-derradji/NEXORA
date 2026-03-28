import asyncio
from typing import Optional
from datetime import datetime

from api.websocket.alerts_ws import alert_ws_manager


async def broadcast_alert(alert_data: dict):
    message = {
        "type": "new_alert",
        "data": {
            "id": alert_data.get("id"),
            "message": alert_data.get("message") or alert_data.get("alert_message"),
            "alert_message": alert_data.get("message") or alert_data.get("alert_message"),
            "severity": alert_data.get("severity") or alert_data.get("alert_level", "INFO"),
            "alert_level": alert_data.get("severity") or alert_data.get("alert_level", "INFO"),
            "device_id": alert_data.get("device_id"),
            "device_hostname": alert_data.get("device_hostname"),
            "device_ip": alert_data.get("device_ip"),
            "device_mac": alert_data.get("device_mac"),
            "timestamp": alert_data.get("timestamp") or datetime.utcnow().isoformat()
        }
    }

    await alert_ws_manager.broadcast(message)


def broadcast_alert_sync(alert_data: dict):
    try:
        asyncio.create_task(broadcast_alert(alert_data))
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except ImportError:
            pass
        asyncio.get_event_loop().run_until_complete(broadcast_alert(alert_data))
