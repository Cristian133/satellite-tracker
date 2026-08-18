"""Lógica compartida para calcular la posición actual de cada satélite
trackeado.

La usan tanto el endpoint REST (`GET /satellites/positions`) como el
broadcaster del WebSocket, para que no diverjan en cómo manejan un TLE que
falla al propagarse (antes el WS salteaba el satélite con problemas y el
REST tiraba un 500 para toda la respuesta)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Satellite
from app.propagation import propagate
from app.schemas import SatellitePosition


async def get_current_positions(db: AsyncSession) -> list[SatellitePosition]:
    result = await db.execute(select(Satellite))
    satellites = result.scalars().all()

    positions = []
    for sat in satellites:
        try:
            lat, lon, alt, vel = propagate(sat.tle_line1, sat.tle_line2, sat.name)
        except Exception:
            # TLE corrupto o satélite decayido: lo salteamos en vez de romper
            # la respuesta completa por un solo satélite con problemas.
            continue
        positions.append(
            SatellitePosition(
                norad_id=sat.norad_id,
                name=sat.name,
                latitude=lat,
                longitude=lon,
                altitude_km=alt,
                velocity_km_s=vel,
                timestamp=datetime.now(timezone.utc),
            )
        )
    return positions
