"""Fan-out del WebSocket /ws/positions.

Antes, cada cliente conectado abría su propia sesión de DB y recalculaba
SGP4 para todos los satélites cada 2 segundos, en paralelo e independiente
del resto de los clientes: con N conexiones activas eso son N queries y N
propagaciones redundantes por tick.

Este módulo lo reemplaza por un único loop en background que calcula las
posiciones una vez por tick y las difunde a todos los clientes conectados.
El costo por tick pasa a ser constante, sin importar cuántos navegadores
estén mirando.
"""

import asyncio

from fastapi import WebSocket

from app.database import async_session
from app.positions import get_current_positions

PUSH_INTERVAL_SECONDS = 2


def _payload(positions) -> dict:
    return {"satellites": [p.model_dump(mode="json") for p in positions]}


class PositionsBroadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def send_snapshot(self, websocket: WebSocket) -> None:
        """Le manda a un cliente recién conectado una foto actual, para que
        no tenga que esperar hasta PUSH_INTERVAL_SECONDS para su primer
        mensaje."""
        async with async_session() as db:
            positions = await get_current_positions(db)
        await websocket.send_json(_payload(positions))

    async def broadcast_forever(self) -> None:
        """Corre durante toda la vida de la app: calcula las posiciones una
        vez por tick y las manda a cada cliente conectado."""
        while True:
            await asyncio.sleep(PUSH_INTERVAL_SECONDS)
            if not self._connections:
                continue  # nadie escuchando, no vale la pena consultar la DB

            async with async_session() as db:
                positions = await get_current_positions(db)
            payload = _payload(positions)

            for websocket in list(self._connections):
                try:
                    await websocket.send_json(payload)
                except Exception:
                    # Cliente que se cayó sin que todavía lo detectemos del
                    # lado del receive(): lo sacamos del set.
                    self.disconnect(websocket)


broadcaster = PositionsBroadcaster()
