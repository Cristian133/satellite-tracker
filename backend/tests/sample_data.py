"""Shared TLE fixtures used across the test suite.

These are real (historical) TLEs. They don't need to be current — tests
propagate them relative to their own epoch rather than to "now" — but using
real data keeps the numbers (altitude, velocity) realistic.
"""

from datetime import datetime, timedelta, timezone

ISS_NORAD_ID = 25544
ISS_NAME = "ISS (ZARYA)"
ISS_LINE1 = "1 25544U 98067A   24025.51782528  .00016717  00000+0  30419-3 0  9993"
ISS_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560088430893"

CSS_NORAD_ID = 48274
CSS_NAME = "CSS (TIANHE)"
CSS_LINE1 = "1 48274U 21035A   24025.55403499  .00007086  00000+0  13061-3 0  9992"
CSS_LINE2 = "2 48274  41.4682  56.5058 0005733 274.5642  85.4832 15.60357728162456"

SAMPLE_TLE_TEXT = f"""{ISS_NAME}
{ISS_LINE1}
{ISS_LINE2}
{CSS_NAME}
{CSS_LINE1}
{CSS_LINE2}
"""


def tle_epoch(line1: str) -> datetime:
    """Parses the YYDDD.DDDDDDDD epoch embedded in a TLE's first line."""
    epoch_str = line1[18:32]
    year = int(epoch_str[:2])
    year += 2000 if year < 57 else 1900
    day_of_year = float(epoch_str[2:])
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)
