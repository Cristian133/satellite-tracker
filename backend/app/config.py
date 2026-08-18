from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://satuser:satpass@localhost:5432/satellites"
    redis_url: str = "redis://localhost:6379/0"

    # CATNR=25544 = solo la ISS. Grupos completos (ej. GROUP=stations) en
    # https://celestrak.org/NORAD/elements/
    celestrak_url: str = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
    tle_refresh_minutes: int = 120

    # Nominatim (OpenStreetMap) para geocoding de ciudad/provincia/país.
    # Uso público: requiere un User-Agent identificable y no admite ráfagas
    # (máx. ~1 req/seg), por eso solo se llama on-demand desde el buscador.
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    nominatim_user_agent: str = "satellite-tracker/1.0 (dev local)"

    # Open-Meteo: pronóstico horario gratuito, sin API key.
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"

    class Config:
        env_file = ".env"


settings = Settings()
