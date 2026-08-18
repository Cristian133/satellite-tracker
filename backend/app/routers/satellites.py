from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Satellite
from app.positions import get_current_positions, get_ground_track
from app.schemas import GroundTrackPoint, SatelliteOut, SatellitePosition
from app.tle_fetcher import fetch_and_store_tles

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("", response_model=list[SatelliteOut])
async def list_satellites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite))
    return result.scalars().all()


@router.get("/positions", response_model=list[SatellitePosition])
async def current_positions(db: AsyncSession = Depends(get_db)):
    return await get_current_positions(db)


@router.post("/refresh")
async def refresh_tles(db: AsyncSession = Depends(get_db)):
    count = await fetch_and_store_tles(db)
    return {"updated": count}


@router.get("/{norad_id}/ground-track", response_model=list[GroundTrackPoint])
async def satellite_ground_track(norad_id: int, db: AsyncSession = Depends(get_db)):
    track = await get_ground_track(db, norad_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return track
