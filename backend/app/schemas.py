from datetime import datetime

from pydantic import BaseModel


class SatelliteOut(BaseModel):
    norad_id: int
    name: str
    updated_at: datetime

    class Config:
        from_attributes = True


class SatellitePosition(BaseModel):
    norad_id: int
    name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_s: float
    timestamp: datetime


class GroundTrackPoint(BaseModel):
    """Un punto de la traza de órbita: solo lat/lon, sin altitud (se proyecta
    sobre la superficie)."""

    latitude: float
    longitude: float
    timestamp: datetime
