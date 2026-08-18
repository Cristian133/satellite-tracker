from datetime import datetime, timedelta

from app.propagation import ground_track, orbital_period_minutes, propagate
from tests.sample_data import ISS_LINE1, ISS_LINE2, tle_epoch


def test_propagate_returns_a_realistic_iss_position():
    when = tle_epoch(ISS_LINE1)

    lat, lon, alt_km, speed_km_s = propagate(ISS_LINE1, ISS_LINE2, "ISS (ZARYA)", when=when)

    assert -90 <= lat <= 90
    assert -180 <= lon <= 180
    # The ISS orbits at roughly 400-420 km altitude.
    assert 380 <= alt_km <= 430
    # Orbital velocity at that altitude is close to 7.66 km/s.
    assert 7.5 <= speed_km_s <= 7.8


def test_propagate_position_changes_over_time():
    t0 = tle_epoch(ISS_LINE1)
    t1 = t0 + timedelta(minutes=10)

    pos0 = propagate(ISS_LINE1, ISS_LINE2, "ISS", when=t0)
    pos1 = propagate(ISS_LINE1, ISS_LINE2, "ISS", when=t1)

    assert pos0 != pos1


def test_propagate_defaults_to_now_when_no_time_is_given(monkeypatch):
    # Pin "now" to the TLE's own epoch so the propagation stays valid
    # regardless of how much time has passed since this TLE was recorded.
    fixed_now = tle_epoch(ISS_LINE1) + timedelta(minutes=5)

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("app.propagation.datetime", _FixedDatetime)

    lat, lon, alt_km, speed_km_s = propagate(ISS_LINE1, ISS_LINE2, "ISS")

    assert -90 <= lat <= 90
    assert -180 <= lon <= 180
    assert 380 <= alt_km <= 430


def test_orbital_period_matches_the_iss_known_period():
    period = orbital_period_minutes(ISS_LINE1, ISS_LINE2, "ISS (ZARYA)")

    # La ISS orbita cada ~92-93 minutos.
    assert 90 <= period <= 95


def test_ground_track_samples_one_full_period_centered_on_when():
    when = tle_epoch(ISS_LINE1)
    period = orbital_period_minutes(ISS_LINE1, ISS_LINE2, "ISS (ZARYA)")

    track = ground_track(ISS_LINE1, ISS_LINE2, "ISS (ZARYA)", samples=10, when=when)

    assert len(track) == 10
    first_t, first_lat, first_lon = track[0]
    last_t, last_lat, last_lon = track[-1]
    assert abs((first_t - (when - timedelta(minutes=period / 2))).total_seconds()) < 1
    assert abs((last_t - (when + timedelta(minutes=period / 2))).total_seconds()) < 1
    for _t, lat, lon in track:
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180


def test_ground_track_points_are_ordered_in_time():
    when = tle_epoch(ISS_LINE1)

    track = ground_track(ISS_LINE1, ISS_LINE2, "ISS (ZARYA)", samples=5, when=when)

    timestamps = [t for t, _lat, _lon in track]
    assert timestamps == sorted(timestamps)
