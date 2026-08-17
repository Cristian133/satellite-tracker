import httpx
import pytest
import respx
from sqlalchemy import select

from app.config import settings
from app.models import Satellite
from app.tle_fetcher import fetch_and_store_tles
from tests.sample_data import CSS_NORAD_ID, ISS_LINE2, ISS_NORAD_ID, SAMPLE_TLE_TEXT


@respx.mock
async def test_fetch_and_store_creates_new_satellites(db_session):
    respx.get(settings.celestrak_url).mock(return_value=httpx.Response(200, text=SAMPLE_TLE_TEXT))

    count = await fetch_and_store_tles(db_session)

    assert count == 2
    result = await db_session.execute(select(Satellite).order_by(Satellite.norad_id))
    satellites = result.scalars().all()
    assert [s.norad_id for s in satellites] == [ISS_NORAD_ID, CSS_NORAD_ID]
    assert satellites[0].name == "ISS (ZARYA)"


@respx.mock
async def test_fetch_and_store_updates_existing_satellite_in_place(db_session):
    respx.get(settings.celestrak_url).mock(return_value=httpx.Response(200, text=SAMPLE_TLE_TEXT))
    await fetch_and_store_tles(db_session)

    updated_line2 = ISS_LINE2.replace("130.5360", "199.9999")
    updated_text = SAMPLE_TLE_TEXT.replace(ISS_LINE2, updated_line2)
    respx.get(settings.celestrak_url).mock(return_value=httpx.Response(200, text=updated_text))
    count = await fetch_and_store_tles(db_session)

    assert count == 2
    result = await db_session.execute(select(Satellite))
    satellites = result.scalars().all()
    # No duplicate row was created for the satellite that already existed.
    assert len(satellites) == 2
    updated = next(s for s in satellites if s.norad_id == ISS_NORAD_ID)
    assert updated.tle_line2 == updated_line2


@respx.mock
async def test_fetch_and_store_skips_malformed_entries(db_session):
    malformed = "BAD SAT\nnot a valid tle line\nalso not valid\n"
    respx.get(settings.celestrak_url).mock(return_value=httpx.Response(200, text=malformed))

    count = await fetch_and_store_tles(db_session)

    assert count == 0
    result = await db_session.execute(select(Satellite))
    assert result.scalars().all() == []


@respx.mock
async def test_fetch_and_store_raises_on_http_error(db_session):
    respx.get(settings.celestrak_url).mock(return_value=httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_and_store_tles(db_session)

    assert exc_info.value.response.status_code == 503
