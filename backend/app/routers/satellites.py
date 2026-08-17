from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Satellite
from app.propagation import propagate
from app.schemas import SatelliteOut, SatellitePosition
from app.tle_fetcher import fetch_and_store_tles

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("", response_model=list[SatelliteOut])
async def list_satellites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite))
    return result.scalars().all()


@router.get("/positions", response_model=list[SatellitePosition])
async def current_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite))
    satellites = result.scalars().all()

    positions = []
    for sat in satellites:
        lat, lon, alt, vel = propagate(sat.tle_line1, sat.tle_line2, sat.name)
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


@router.post("/refresh")
async def refresh_tles(db: AsyncSession = Depends(get_db)):
    count = await fetch_and_store_tles(db)
    return {"updated": count}
