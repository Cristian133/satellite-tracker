from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://satuser:satpass@localhost:5432/satellites"
    redis_url: str = "redis://localhost:6379/0"

    # CATNR=25544 = solo la ISS. Grupos completos (ej. GROUP=stations) en
    # https://celestrak.org/NORAD/elements/
    celestrak_url: str = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
    tle_refresh_minutes: int = 120

    class Config:
        env_file = ".env"


settings = Settings()
