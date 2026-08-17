"""WebSocket tests for /ws/positions.

Starlette's TestClient drives the websocket from its own thread/event loop,
separate from the one pytest-asyncio uses for the rest of the suite. Mixing
that with the shared async engine/session used elsewhere would break
aiosqlite (a connection can't hop event loops), so this test seeds data with
a plain sqlite3 connection instead of the async `db_session` fixture, and
uses a bare `TestClient(app)` (not as a context manager, which would trigger
the real app lifespan — hitting the network and starting the scheduler).
"""

import sqlite3

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from tests.sample_data import ISS_LINE1, ISS_LINE2, ISS_NAME, ISS_NORAD_ID


def _sqlite_path() -> str:
    # e.g. "sqlite+aiosqlite:///./.pytest_satellite_tracker.db" -> "./.pytest_satellite_tracker.db"
    return settings.database_url.split("///", 1)[1]


def _seed_iss_via_raw_sqlite():
    conn = sqlite3.connect(_sqlite_path())
    try:
        conn.execute(
            "INSERT INTO satellites (norad_id, name, tle_line1, tle_line2, updated_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (ISS_NORAD_ID, ISS_NAME, ISS_LINE1, ISS_LINE2),
        )
        conn.commit()
    finally:
        conn.close()


def test_positions_stream_sends_the_current_satellite():
    _seed_iss_via_raw_sqlite()

    with TestClient(app).websocket_connect("/ws/positions") as websocket:
        message = websocket.receive_json()

    assert "satellites" in message
    assert len(message["satellites"]) == 1
    satellite = message["satellites"][0]
    assert satellite["norad_id"] == ISS_NORAD_ID
    assert satellite["name"] == ISS_NAME
    assert -90 <= satellite["latitude"] <= 90
    assert -180 <= satellite["longitude"] <= 180


def test_positions_stream_sends_empty_list_when_no_satellites_tracked():
    with TestClient(app).websocket_connect("/ws/positions") as websocket:
        message = websocket.receive_json()

    assert message == {"satellites": []}
