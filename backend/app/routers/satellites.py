from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Satellite
from app.positions import get_current_positions, get_ground_track, get_next_visible_pass
from app.schemas import GroundTrackPoint, SatelliteOut, SatellitePosition, VisiblePass
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


@router.get("/{norad_id}/next-visible-pass", response_model=VisiblePass | None)
async def satellite_next_visible_pass(
    norad_id: int,
    latitude: float = Query(..., ge=-90, le=90, description="Latitud del observador, en grados"),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitud del observador, en grados"
    ),
    elevation_m: float = Query(
        0.0, description="Elevación del observador sobre el nivel del mar, en metros"
    ),
    min_elevation_deg: float = Query(
        10.0,
        ge=0,
        le=90,
        description="Elevación mínima sobre el horizonte para que el pase cuente",
    ),
    search_days: float = Query(10.0, gt=0, le=30, description="Cuántos días adelante buscar"),
    db: AsyncSession = Depends(get_db),
):
    tracked, visible_pass = await get_next_visible_pass(
        db, norad_id, latitude, longitude, elevation_m, min_elevation_deg, search_days
    )
    if not tracked:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return visible_pass
