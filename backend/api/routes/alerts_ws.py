from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging

from api.websocket.alerts_ws import alert_ws_manager

logger = logging.getLogger("alerts_ws_router")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await alert_ws_manager.connect(websocket)
    logger.info("Client connected to /ws/alerts")

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

            await websocket.send_json({"status": "connected", "type": "alert_channel"})

    except WebSocketDisconnect:
        alert_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from /ws/alerts")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        alert_ws_manager.disconnect(websocket)
