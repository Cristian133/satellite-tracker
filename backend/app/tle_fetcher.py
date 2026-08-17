import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Satellite


async def fetch_and_store_tles(db: AsyncSession) -> int:
    """Descarga el set de TLEs de Celestrak y hace upsert en la base."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(settings.celestrak_url)
        resp.raise_for_status()
        lines = [line.strip() for line in resp.text.splitlines() if line.strip()]

    count = 0
    for i in range(0, len(lines) - 2, 3):
        name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
        if not (line1.startswith("1 ") and line2.startswith("2 ")):
            continue
        norad_id = int(line1[2:7])

        result = await db.execute(select(Satellite).where(Satellite.norad_id == norad_id))
        sat = result.scalar_one_or_none()
        if sat is None:
            sat = Satellite(norad_id=norad_id, name=name, tle_line1=line1, tle_line2=line2)
            db.add(sat)
        else:
            sat.name = name
            sat.tle_line1 = line1
            sat.tle_line2 = line2
        count += 1

    await db.commit()
    return count
