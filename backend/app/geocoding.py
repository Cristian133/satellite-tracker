import httpx

from app.config import settings
from app.schemas import GeocodeResult


async def geocode_place(query: str, limit: int = 5) -> list[GeocodeResult]:
    """Resuelve una ciudad/provincia/país en texto libre (ej. "Rosario, Santa Fe,
    Argentina") a una lista de coordenadas candidatas, vía Nominatim."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            settings.nominatim_url,
            params={"q": query, "format": "jsonv2", "limit": limit},
            headers={"User-Agent": settings.nominatim_user_agent},
        )
        response.raise_for_status()
        results = response.json()

    return [
        GeocodeResult(
            display_name=item["display_name"],
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
        )
        for item in results
    ]
