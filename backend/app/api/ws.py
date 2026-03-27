from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.broadcaster import register, unregister

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register(websocket)
    try:
        while True:
            # Keep connection alive; client sends pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        unregister(websocket)
