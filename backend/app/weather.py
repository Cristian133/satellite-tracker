import math
from datetime import UTC, datetime

import httpx

from app.config import settings
from app.schemas import WeatherForecast

# Códigos WMO que devuelve Open-Meteo (weather_code), traducidos a una
# descripción corta en español. No es una lista exhaustiva del estándar,
# solo los valores que Open-Meteo efectivamente emite.
_WEATHER_CODE_DESCRIPTIONS: dict[int, str] = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna débil",
    53: "Llovizna moderada",
    55: "Llovizna intensa",
    56: "Llovizna helada débil",
    57: "Llovizna helada intensa",
    61: "Lluvia débil",
    63: "Lluvia moderada",
    65: "Lluvia intensa",
    66: "Lluvia helada débil",
    67: "Lluvia helada intensa",
    71: "Nevada débil",
    73: "Nevada moderada",
    75: "Nevada intensa",
    77: "Granizo pequeño",
    80: "Chubascos débiles",
    81: "Chubascos moderados",
    82: "Chubascos intensos",
    85: "Chubascos de nieve débiles",
    86: "Chubascos de nieve intensos",
    95: "Tormenta eléctrica",
    96: "Tormenta con granizo débil",
    99: "Tormenta con granizo intenso",
}


def _describe(weather_code: int) -> str:
    return _WEATHER_CODE_DESCRIPTIONS.get(weather_code, "Sin datos")


async def get_forecast_at(
    latitude: float, longitude: float, when: datetime
) -> WeatherForecast | None:
    """Pronóstico horario de Open-Meteo para (latitude, longitude), evaluado
    en la hora más cercana a `when`. Devuelve None si `when` cae fuera del
    rango de pronóstico disponible (Open-Meteo ofrece como máximo 16 días) o
    si la API no responde."""
    now = datetime.now(UTC)
    days_ahead = (when - now).days
    if days_ahead < 0 or days_ahead > 16:
        return None
    # +2 de margen para no quedar corto por redondeos de días/horas.
    forecast_days = min(16, max(1, days_ahead + 2))

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                settings.open_meteo_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "temperature_2m,cloud_cover,precipitation_probability,weather_code",
                    "timezone": "UTC",
                    "forecast_days": forecast_days,
                },
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return None

    # Cada entrada es "YYYY-MM-DDTHH:MM" en UTC (timezone=UTC pedido arriba).
    parsed_times = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in times]
    closest_idx = min(
        range(len(parsed_times)),
        key=lambda i: math.fabs((parsed_times[i] - when).total_seconds()),
    )

    try:
        return WeatherForecast(
            timestamp=parsed_times[closest_idx],
            temperature_c=hourly["temperature_2m"][closest_idx],
            cloud_cover_pct=hourly["cloud_cover"][closest_idx],
            precipitation_probability_pct=hourly["precipitation_probability"][closest_idx],
            description=_describe(hourly["weather_code"][closest_idx]),
        )
    except (KeyError, IndexError, TypeError):
        return None
