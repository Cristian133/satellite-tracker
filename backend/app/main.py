from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, async_session, engine
from app.routers import satellites, ws
from app.scheduler import start_scheduler
from app.tle_fetcher import fetch_and_store_tles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas si no existen. Para un proyecto real, reemplazar por
    # migraciones con Alembic.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Carga inicial de TLEs para no arrancar con la base vacía.
    async with async_session() as db:
        await fetch_and_store_tles(db)

    start_scheduler()
    yield


app = FastAPI(title="Satellite Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satellites.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
