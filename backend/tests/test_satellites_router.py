from datetime import datetime

from app.models import Satellite
from tests.sample_data import ISS_LINE1, ISS_LINE2, ISS_NAME, ISS_NORAD_ID, tle_epoch


async def _seed_iss(db_session):
    db_session.add(
        Satellite(norad_id=ISS_NORAD_ID, name=ISS_NAME, tle_line1=ISS_LINE1, tle_line2=ISS_LINE2)
    )
    await db_session.commit()


def _pin_now_to_the_tle_epoch(monkeypatch):
    """Ancla datetime.now() al epoch del TLE de prueba: un pase buscado
    relativo a "ahora" en la vida real estaría propagando ~2 años más allá
    del epoch, donde SGP4 ya no es confiable y la búsqueda se vuelve
    impredecible. Igual que en test_propagation.py."""
    fixed_now = tle_epoch(ISS_LINE1)

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("app.propagation.datetime", _FixedDatetime)


async def test_list_satellites_returns_empty_list_when_none_tracked(client):
    resp = await client.get("/satellites")

    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_satellites_returns_seeded_data(client, db_session):
    await _seed_iss(db_session)

    resp = await client.get("/satellites")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["norad_id"] == ISS_NORAD_ID
    assert body[0]["name"] == ISS_NAME
    assert "updated_at" in body[0]


async def test_positions_returns_propagated_data_for_each_satellite(client, db_session):
    await _seed_iss(db_session)

    resp = await client.get("/satellites/positions")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    position = body[0]
    assert position["norad_id"] == ISS_NORAD_ID
    assert position["name"] == ISS_NAME
    assert -90 <= position["latitude"] <= 90
    assert -180 <= position["longitude"] <= 180
    assert position["altitude_km"] > 0
    assert position["velocity_km_s"] > 0
    assert "timestamp" in position


async def test_positions_returns_empty_list_when_no_satellites_tracked(client):
    resp = await client.get("/satellites/positions")

    assert resp.status_code == 200
    assert resp.json() == []


async def test_refresh_endpoint_delegates_to_tle_fetcher_and_returns_count(client, monkeypatch):
    async def fake_fetch_and_store_tles(db):
        return 3

    monkeypatch.setattr(
        "app.routers.satellites.fetch_and_store_tles", fake_fetch_and_store_tles
    )

    resp = await client.post("/satellites/refresh")

    assert resp.status_code == 200
    assert resp.json() == {"updated": 3}


async def test_health_check(client):
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ground_track_returns_404_for_an_untracked_satellite(client):
    resp = await client.get("/satellites/99999/ground-track")

    assert resp.status_code == 404


async def test_ground_track_returns_sampled_points_for_a_tracked_satellite(client, db_session):
    await _seed_iss(db_session)

    resp = await client.get(f"/satellites/{ISS_NORAD_ID}/ground-track")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 120  # default de ground_track()
    for point in body:
        assert -90 <= point["latitude"] <= 90
        assert -180 <= point["longitude"] <= 180
        assert "timestamp" in point
    # Los puntos están ordenados en el tiempo.
    timestamps = [point["timestamp"] for point in body]
    assert timestamps == sorted(timestamps)


async def test_next_visible_pass_returns_404_for_an_untracked_satellite(client):
    resp = await client.get(
        "/satellites/99999/next-visible-pass", params={"latitude": 40.7, "longitude": -74.0}
    )

    assert resp.status_code == 404


async def test_next_visible_pass_requires_latitude_and_longitude(client, db_session):
    await _seed_iss(db_session)

    resp = await client.get(f"/satellites/{ISS_NORAD_ID}/next-visible-pass")

    assert resp.status_code == 422


async def test_next_visible_pass_returns_a_pass_for_a_tracked_satellite(
    client, db_session, monkeypatch
):
    await _seed_iss(db_session)
    _pin_now_to_the_tle_epoch(monkeypatch)

    resp = await client.get(
        f"/satellites/{ISS_NORAD_ID}/next-visible-pass",
        params={"latitude": 40.7, "longitude": -74.0, "search_days": 30},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body is not None
    assert body["rise_time"] < body["culminate_time"] < body["set_time"]
    assert body["max_elevation_deg"] >= 10
    assert 0 <= body["azimuth_deg"] < 360


async def test_next_visible_pass_returns_null_when_none_matches_the_threshold(
    client, db_session, monkeypatch
):
    await _seed_iss(db_session)
    _pin_now_to_the_tle_epoch(monkeypatch)

    resp = await client.get(
        f"/satellites/{ISS_NORAD_ID}/next-visible-pass",
        params={"latitude": 40.7, "longitude": -74.0, "search_days": 3, "min_elevation_deg": 89},
    )

    assert resp.status_code == 200
    assert resp.json() is None
