from datetime import UTC, datetime, timedelta

import httpx
import respx

from app.config import settings
from app.weather import get_forecast_at


def _sample_response(base: datetime, hours: int = 48):
    times = [(base + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(hours)]
    return {
        "hourly": {
            "time": times,
            "temperature_2m": [15.0 + i * 0.1 for i in range(hours)],
            "cloud_cover": [10.0 + i for i in range(hours)],
            "precipitation_probability": [0.0 for _ in range(hours)],
            "weather_code": [0 for _ in range(hours)],
        }
    }


@respx.mock
async def test_get_forecast_at_returns_the_closest_hour():
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    respx.get(settings.open_meteo_url).mock(
        return_value=httpx.Response(200, json=_sample_response(now))
    )

    when = now + timedelta(hours=5, minutes=20)
    forecast = await get_forecast_at(40.7, -74.0, when)

    assert forecast is not None
    assert forecast.timestamp == now + timedelta(hours=5)
    assert forecast.temperature_c == 15.5
    assert forecast.description == "Despejado"


@respx.mock
async def test_get_forecast_at_maps_known_weather_codes():
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    body = _sample_response(now)
    body["hourly"]["weather_code"][3] = 61
    respx.get(settings.open_meteo_url).mock(return_value=httpx.Response(200, json=body))

    forecast = await get_forecast_at(40.7, -74.0, now + timedelta(hours=3))

    assert forecast is not None
    assert forecast.description == "Lluvia débil"


async def test_get_forecast_at_returns_none_when_the_date_is_out_of_range():
    when = datetime.now(UTC) + timedelta(days=20)

    forecast = await get_forecast_at(40.7, -74.0, when)

    assert forecast is None


async def test_get_forecast_at_returns_none_for_a_past_date():
    when = datetime.now(UTC) - timedelta(days=1)

    forecast = await get_forecast_at(40.7, -74.0, when)

    assert forecast is None


@respx.mock
async def test_get_forecast_at_returns_none_on_http_error():
    respx.get(settings.open_meteo_url).mock(return_value=httpx.Response(503))

    forecast = await get_forecast_at(40.7, -74.0, datetime.now(UTC) + timedelta(hours=1))

    assert forecast is None
