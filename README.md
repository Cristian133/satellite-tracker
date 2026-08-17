# Satellite Tracker

Tracking de satélites en tiempo real: TLE (Celestrak) → propagación orbital SGP4 (skyfield) → WebSocket → globo 3D (CesiumJS).

## Estructura

```
satellite-tracker/
├── docker-compose.yml
├── .env.example
├── backend/                   # FastAPI + skyfield + Postgres + Redis
│   ├── app/
│   │   ├── main.py            # app FastAPI, lifespan (crea tablas, carga TLEs iniciales, scheduler)
│   │   ├── config.py          # settings (env vars)
│   │   ├── database.py        # engine/session async de SQLAlchemy
│   │   ├── models.py          # tabla Satellite (norad_id, TLE)
│   │   ├── schemas.py         # DTOs Pydantic
│   │   ├── tle_fetcher.py     # descarga TLEs de Celestrak y upsert en DB
│   │   ├── propagation.py     # SGP4 vía skyfield -> lat/lon/alt/velocidad
│   │   ├── scheduler.py       # refresco periódico de TLEs (APScheduler)
│   │   └── routers/
│   │       ├── satellites.py  # GET /satellites, GET /satellites/positions, POST /satellites/refresh
│   │       └── ws.py          # WS /ws/positions (push cada 2s)
│   └── requirements.txt
└── frontend/                  # React + TypeScript + CesiumJS (Resium)
    └── src/
        ├── App.tsx
        ├── components/Globe.tsx       # globo Cesium con entidades de satélites
        ├── hooks/useSatelliteSocket.ts # cliente WebSocket con reconexión
        └── types/satellite.ts
```

## Cómo levantarlo

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env
```

(Opcional pero recomendado) conseguí un token gratuito en https://ion.cesium.com y ponelo en `CESIUM_ION_TOKEN` dentro de `.env` — sin token, Cesium usa un demo token compartido con rate limit muy bajo.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend (docs OpenAPI): http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/positions

Al arrancar, el backend crea las tablas, descarga el grupo de TLEs "stations" (ISS, Tiangong, etc. — configurable en `app/config.py`) y arranca un job que lo refresca cada 2 horas. El frontend se conecta por WebSocket y va posicionando cada satélite en el globo.

## Próximos pasos sugeridos

- **Migraciones**: reemplazar el `create_all` en el lifespan por Alembic.
- **Históricos**: si vas a guardar series temporales de posiciones, sumar TimescaleDB (extensión de Postgres) en vez de recalcular siempre en caliente.
- **Más satélites**: cambiar `CELESTRAK_URL` en `.env`/`config.py` por otro grupo (`active`, `visual`, `gps-ops`, etc. — ver https://celestrak.org/NORAD/elements/).
- **Cálculo de pases visibles**: skyfield permite calcular pases sobre una ubicación del observador (elevación/azimut) — útil para "próximo pase visible de la ISS sobre tu ciudad".
- **Autenticación** si el proyecto deja de ser solo lectura pública.
- **Tests**: pytest + httpx para el backend; Vitest/Testing Library para el frontend.
