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
from app.propagation import ground_track, next_visible_pass, propagate
from app.schemas import GroundTrackPoint, SatellitePosition, VisiblePass


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


async def get_ground_track(db: AsyncSession, norad_id: int) -> list[GroundTrackPoint] | None:
    """Devuelve la traza de órbita del satélite, o None si no está trackeado."""
    result = await db.execute(select(Satellite).where(Satellite.norad_id == norad_id))
    sat = result.scalar_one_or_none()
    if sat is None:
        return None

    track = ground_track(sat.tle_line1, sat.tle_line2, sat.name)
    return [
        GroundTrackPoint(latitude=lat, longitude=lon, timestamp=t) for t, lat, lon in track
    ]


async def get_next_visible_pass(
    db: AsyncSession,
    norad_id: int,
    latitude: float,
    longitude: float,
    elevation_m: float = 0.0,
    min_elevation_deg: float = 10.0,
    search_days: float = 10.0,
) -> tuple[bool, VisiblePass | None]:
    """Devuelve (satélite_trackeado, próximo_pase_visible). El segundo
    elemento es None tanto si el satélite no está trackeado como si no hay
    ningún pase visible dentro de la ventana de búsqueda — usar el primero
    para distinguir esos dos casos."""
    result = await db.execute(select(Satellite).where(Satellite.norad_id == norad_id))
    sat = result.scalar_one_or_none()
    if sat is None:
        return False, None

    raw = next_visible_pass(
        sat.tle_line1,
        sat.tle_line2,
        sat.name,
        latitude,
        longitude,
        elevation_m,
        search_days=search_days,
        min_elevation_deg=min_elevation_deg,
    )
    return True, VisiblePass(**raw) if raw is not None else None
