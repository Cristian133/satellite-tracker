import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models import Satellite
from app.propagation import propagate

router = APIRouter()

PUSH_INTERVAL_SECONDS = 2


@router.websocket("/ws/positions")
async def positions_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            async with async_session() as db:
                result = await db.execute(select(Satellite))
                satellites = result.scalars().all()

            payload = []
            for sat in satellites:
                try:
                    lat, lon, alt, vel = propagate(sat.tle_line1, sat.tle_line2, sat.name)
                except Exception:
                    continue
                payload.append(
                    {
                        "norad_id": sat.norad_id,
                        "name": sat.name,
                        "latitude": lat,
                        "longitude": lon,
                        "altitude_km": alt,
                        "velocity_km_s": vel,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            await websocket.send_json({"satellites": payload})
            await asyncio.sleep(PUSH_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        pass
