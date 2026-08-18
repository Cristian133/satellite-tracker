"""Propagación orbital SGP4 vía skyfield (wrapper de alto nivel sobre sgp4
que ya resuelve la conversión TEME -> geodésica WGS84 correctamente)."""

import math
from datetime import UTC, datetime, timedelta

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
    when = when or datetime.now(UTC)
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
    when = when or datetime.now(UTC)
    half_period = timedelta(minutes=orbital_period_minutes(tle_line1, tle_line2, name) / 2)
    start = when - half_period
    step = (2 * half_period) / (samples - 1)

    points = []
    for i in range(samples):
        t = start + step * i
        lat, lon, _alt_km, _speed = propagate(tle_line1, tle_line2, name, when=t)
        points.append((t, lat, lon))
    return points


_eph = None


def _ephemeris():
    """Carga (y cachea en memoria para el resto del proceso) la efeméride
    solar de421, necesaria para saber si el satélite está iluminado por el
    sol y si el observador está de noche. La primera vez la descarga de la
    red (~17MB) y la deja cacheada en disco (de421.bsp, en el directorio de
    trabajo) para las corridas siguientes."""
    global _eph
    if _eph is None:
        _eph = load("de421.bsp")
    return _eph


def next_visible_pass(
    tle_line1: str,
    tle_line2: str,
    name: str,
    latitude: float,
    longitude: float,
    elevation_m: float = 0.0,
    when: datetime | None = None,
    search_days: float = 10.0,
    min_elevation_deg: float = 10.0,
) -> dict | None:
    """Busca el próximo pase VISIBLE del satélite para un observador en
    (latitude, longitude, elevation_m) — no solo "sobre el horizonte", sino
    realmente mirable a ojo desnudo: exige que el satélite esté por encima
    de `min_elevation_deg`, que esté iluminado por el sol, y que el
    observador ya esté en penumbra u oscuridad (sol a más de 6° bajo el
    horizonte, arranque del crepúsculo civil). Devuelve None si no
    encuentra ninguno dentro de `search_days`."""
    when = when or datetime.now(UTC)
    satellite = EarthSatellite(tle_line1, tle_line2, name, _ts)
    observer = wgs84.latlon(latitude, longitude, elevation_m)
    eph = _ephemeris()
    sun = eph["sun"]
    earth = eph["earth"]

    t0 = _ts.from_datetime(when)
    t1 = _ts.from_datetime(when + timedelta(days=search_days))
    times, events = satellite.find_events(observer, t0, t1, altitude_degrees=min_elevation_deg)

    # events: 0 = sale por el horizonte, 1 = culmina, 2 = se pone. Los
    # recorremos de a tríos consecutivos (rise, culminate, set); si la
    # ventana de búsqueda corta un pase a la mitad, ese trío queda
    # incompleto y lo salteamos en vez de romper.
    i = 0
    while i + 2 < len(events):
        if not (events[i] == 0 and events[i + 1] == 1 and events[i + 2] == 2):
            i += 1
            continue
        rise_t, culminate_t, set_t = times[i], times[i + 1], times[i + 2]

        sun_alt, _sun_az, _sun_dist = (
            (earth + observer).at(culminate_t).observe(sun).apparent().altaz()
        )
        is_dark_enough = sun_alt.degrees <= -6
        is_satellite_sunlit = satellite.at(culminate_t).is_sunlit(eph)

        if is_dark_enough and is_satellite_sunlit:
            alt, az, _distance = (satellite - observer).at(culminate_t).altaz()
            return {
                "rise_time": rise_t.utc_datetime(),
                "culminate_time": culminate_t.utc_datetime(),
                "set_time": set_t.utc_datetime(),
                "max_elevation_deg": alt.degrees,
                "azimuth_deg": az.degrees,
            }
        i += 3

    return None
