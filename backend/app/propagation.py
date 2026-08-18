"""Propagación orbital SGP4 vía skyfield (wrapper de alto nivel sobre sgp4
que ya resuelve la conversión TEME -> geodésica WGS84 correctamente)."""

import math
from datetime import datetime, timedelta, timezone

from skyfield.api import EarthSatellite, load, wgs84

# builtin=True evita que skyfield intente descargar tablas de tiempo (leap
# seconds, delta-T) por red la primera vez que corre.
_ts = load.timescale(builtin=True)


def propagate(
    tle_line1: str,
    tle_line2: str,
    name: str = "SAT",
    when: datetime | None = None,
) -> tuple[float, float, float, float]:
    """Devuelve (lat_deg, lon_deg, alt_km, velocidad_km_s) para un TLE en un instante UTC dado."""
    when = when or datetime.now(timezone.utc)
    satellite = EarthSatellite(tle_line1, tle_line2, name, _ts)

    t = _ts.from_datetime(when)
    geocentric = satellite.at(t)
    subpoint = wgs84.subpoint(geocentric)

    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    alt_km = subpoint.elevation.km

    vx, vy, vz = geocentric.velocity.km_per_s
    speed = (vx**2 + vy**2 + vz**2) ** 0.5

    return lat, lon, alt_km, speed


def orbital_period_minutes(tle_line1: str, tle_line2: str, name: str = "SAT") -> float:
    """Período orbital en minutos, derivado del movimiento medio (no_kozai,
    en rad/min) que trae el propio TLE."""
    satellite = EarthSatellite(tle_line1, tle_line2, name, _ts)
    return (2 * math.pi) / satellite.model.no_kozai


def ground_track(
    tle_line1: str,
    tle_line2: str,
    name: str = "SAT",
    samples: int = 120,
    when: datetime | None = None,
) -> list[tuple[datetime, float, float]]:
    """Muestrea la traza de órbita (lat/lon del punto subsatelital, sin
    altitud: una ground track se proyecta sobre la superficie) a lo largo de
    un período orbital completo, centrado en `when` (mitad pasado, mitad
    futuro). Devuelve una lista de (instante UTC, lat_deg, lon_deg)."""
    when = when or datetime.now(timezone.utc)
    half_period = timedelta(minutes=orbital_period_minutes(tle_line1, tle_line2, name) / 2)
    start = when - half_period
    step = (2 * half_period) / (samples - 1)

    points = []
    for i in range(samples):
        t = start + step * i
        lat, lon, _alt_km, _speed = propagate(tle_line1, tle_line2, name, when=t)
        points.append((t, lat, lon))
    return points
