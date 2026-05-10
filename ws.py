from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import ws_manager
from app.utils.security import decode_token
from loguru import logger

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/dashboard")
async def ws_dashboard(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """
    Real-time dashboard WebSocket.
    Connect with: ws://host/ws/dashboard?token=<access_token>
    Server pushes events: new_report, hotspot_updated, social_spike
    """
    # Optional auth check
    if token:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await ws_manager.connect(websocket, room="dashboard")
    try:
        await ws_manager.send_personal(websocket, {"type": "connected", "message": "Welcome to INCOIS live dashboard"})
        while True:
            # Keep-alive / receive client messages (e.g. pings)
            data = await websocket.receive_text()
            if data == "ping":
                await ws_manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room="dashboard")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, room="dashboard")
