from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.broadcaster import broadcaster

router = APIRouter()


@router.websocket("/ws/positions")
async def positions_stream(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        await broadcaster.send_snapshot(websocket)
        while True:
            # El cliente nunca manda nada por este socket; el único uso de
            # receive() es bloquear acá hasta que se desconecte, sin hacer
            # polling activo. Las actualizaciones periódicas las empuja el
            # broadcaster compartido, no este handler.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.disconnect(websocket)
