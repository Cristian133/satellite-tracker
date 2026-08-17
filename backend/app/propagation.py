"""Propagación orbital SGP4 vía skyfield (wrapper de alto nivel sobre sgp4
que ya resuelve la conversión TEME -> geodésica WGS84 correctamente)."""

from datetime import datetime, timezone

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
