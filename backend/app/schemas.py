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


class VisiblePass(BaseModel):
    """Un pase visible a ojo desnudo: satélite sobre el horizonte,
    iluminado por el sol, con el observador ya en penumbra/oscuridad."""

    rise_time: datetime
    culminate_time: datetime
    set_time: datetime
    max_elevation_deg: float
    azimuth_deg: float


class GeocodeResult(BaseModel):
    """Resultado de resolver una ciudad/provincia/país a coordenadas."""

    display_name: str
    latitude: float
    longitude: float
