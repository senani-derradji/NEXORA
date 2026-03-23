from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging

from api.websocket.alerts_ws import alert_ws_manager

# Use setup_logger instead of raw logging.getLogger to avoid duplicates
logger = logging.getLogger("alerts_ws_router")
# Ensure no duplicate handlers (check at module level)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts.
    Clients connect to receive instant alerts as they are created.
    """
    await alert_ws_manager.connect(websocket)
    logger.info("Client connected to /ws/alerts")

    try:
        # Keep the connection alive and handle any incoming messages
        while True:
            # Wait for any message from client (could be used for heartbeat or subscriptions)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

            # Echo back acknowledgment (optional)
            await websocket.send_json({"status": "connected", "type": "alert_channel"})

    except WebSocketDisconnect:
        alert_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from /ws/alerts")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        alert_ws_manager.disconnect(websocket)
