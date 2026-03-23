"""
Alert broadcast helper - broadcasts new alerts to all connected WebSocket clients.
"""
import asyncio
from typing import Optional
from datetime import datetime

from api.websocket.alerts_ws import alert_ws_manager


async def broadcast_alert(alert_data: dict):
    """
    Broadcast a new alert to all connected WebSocket clients.

    Args:
        alert_data: Dictionary containing alert information with keys:
            - id: Alert ID
            - message: Alert message
            - severity: Alert severity (CRITICAL, WARNING, INFO)
            - device_hostname: Device hostname
            - device_ip: Device IP address
            - timestamp: Alert timestamp
    """
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
    """
    Synchronous wrapper for broadcast_alert.
    Used when alert creation happens in a non-async context.
    """
    try:
        asyncio.create_task(broadcast_alert(alert_data))
    except RuntimeError:
        # If there's no running event loop, create a new one
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except ImportError:
            pass
        asyncio.get_event_loop().run_until_complete(broadcast_alert(alert_data))
