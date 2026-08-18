from fastapi import APIRouter, HTTPException, Query

from app.geocoding import geocode_place
from app.schemas import GeocodeResult

router = APIRouter(prefix="/geocode", tags=["geocoding"])


@router.get("", response_model=list[GeocodeResult])
async def geocode(
    query: str = Query(
        ..., min_length=2, description='Lugar en texto libre, ej. "Rosario, Santa Fe, Argentina"'
    ),
):
    try:
        results = await geocode_place(query)
    except Exception as exc:  # httpx.HTTPError y variantes
        raise HTTPException(status_code=502, detail="No se pudo resolver la ubicación") from exc
    return results
