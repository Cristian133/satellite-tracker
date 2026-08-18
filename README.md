# 🛰️ Satellite Tracker

Real-time satellite tracking on a 3D globe. TLE data from **Celestrak** is
propagated with **SGP4** (via `skyfield`) on the backend and streamed to the
browser over **WebSocket**, where **CesiumJS** renders each satellite's live
position on an interactive globe.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript&logoColor=white)
![CesiumJS](https://img.shields.io/badge/CesiumJS-1.144-6CADDF?logo=cesium&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

The backend fetches Two-Line Element (TLE) sets from Celestrak, stores them
in Postgres, and propagates each satellite's orbit in real time with SGP4.
Positions are pushed to connected clients over a WebSocket every 2 seconds.
The frontend is a React + TypeScript app that renders the satellites as
entities on a Cesium globe, updating their position live.

```
Celestrak (TLE) → FastAPI + skyfield (SGP4) → WebSocket → CesiumJS globe
                         ↓
                    Postgres (TLE store)
```

## Features

- 🌍 Live 3D globe rendering with CesiumJS / Resium
- 📡 Orbital propagation via SGP4 (`skyfield`), broadcast every 2 seconds
- 🔄 Automatic TLE refresh on a schedule (APScheduler), plus manual refresh
- 🔌 REST API for satellite metadata and current positions
- 🔁 WebSocket client with automatic reconnection
- 🐳 One-command startup with Docker Compose

## Tech Stack

| Layer      | Technology                                             |
|------------|---------------------------------------------------------|
| Backend    | FastAPI, SQLAlchemy (async), asyncpg, Pydantic Settings |
| Propagation| skyfield (SGP4), APScheduler for periodic TLE refresh   |
| Storage    | PostgreSQL, Redis                                       |
| Frontend   | React 18, TypeScript, Vite                              |
| Globe      | CesiumJS via Resium                                     |
| Infra      | Docker Compose                                          |

## Project Structure

```
satellite-tracker/
├── docker-compose.yml
├── .env.example
├── .pre-commit-config.yaml        # lint + tests + build, run on every git commit
├── .github/workflows/ci.yml       # same checks, run on every push (+ Docker image builds)
├── backend/                       # FastAPI + skyfield + Postgres + Redis
│   ├── pyproject.toml              # Ruff config (lint + format)
│   ├── app/
│   │   ├── main.py                # FastAPI app & lifespan (create tables, seed TLEs, start scheduler)
│   │   ├── config.py               # settings (env vars)
│   │   ├── database.py             # async SQLAlchemy engine/session
│   │   ├── models.py                # Satellite table (norad_id, TLE lines)
│   │   ├── schemas.py               # Pydantic DTOs
│   │   ├── tle_fetcher.py           # fetches TLEs from Celestrak and upserts them
│   │   ├── propagation.py           # SGP4 propagation, ground track sampling, visible-pass search
│   │   ├── positions.py             # DB + propagation glue shared by the REST endpoints and the WS broadcaster
│   │   ├── broadcaster.py           # single background loop that fans positions out to every /ws/positions client
│   │   ├── scheduler.py             # periodic TLE refresh (APScheduler)
│   │   └── routers/
│   │       ├── satellites.py        # GET /satellites, .../positions, .../ground-track, .../next-visible-pass, POST .../refresh
│   │       ├── geocoding.py         # GET /geocode (city/province/country -> lat/lon, via Nominatim)
│   │       └── ws.py                # WS /ws/positions (registers/unregisters clients on the shared broadcaster)
│   └── requirements.txt
└── frontend/                      # React + TypeScript + CesiumJS (Resium)
    ├── eslint.config.js            # ESLint config (flat config)
    └── src/
        ├── App.tsx
        ├── components/Globe.tsx              # Cesium globe: satellite entity + ground-track polyline
        ├── components/VisiblePassPanel.tsx   # lat/lon or place-name search -> next visible pass
        ├── hooks/useSatelliteSocket.ts       # WebSocket client with reconnection
        ├── hooks/useGroundTrack.ts           # polls the ground-track endpoint every 5 minutes
        └── types/satellite.ts
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run it

```bash
cp .env.example .env
```

(Optional but recommended) grab a free token at [ion.cesium.com](https://ion.cesium.com)
and set it as `CESIUM_ION_TOKEN` in `.env`. Without a token, Cesium falls
back to a shared demo token with a very low rate limit.

```bash
docker compose up --build
```

| Service                | URL                              |
|-------------------------|-----------------------------------|
| Frontend                | http://localhost:5173            |
| Backend (OpenAPI docs)  | http://localhost:8000/docs       |
| WebSocket               | ws://localhost:8000/ws/positions |

On startup, the backend creates the database tables, downloads the
`stations` TLE group (ISS, Tiangong, etc. — configurable in
`backend/app/config.py`), and starts a background job that refreshes it
every 2 hours. The frontend connects over WebSocket and places each
satellite on the globe as positions arrive.

## API Reference

| Method | Endpoint                | Description                                              |
|--------|--------------------------|------------------------------------------------------------|
| GET    | `/satellites`            | List tracked satellites (NORAD ID, name, last update)      |
| GET    | `/satellites/positions`  | Current propagated position for every satellite            |
| POST   | `/satellites/refresh`    | Force an immediate TLE refresh from Celestrak               |
| GET    | `/satellites/{norad_id}/ground-track` | Sampled ground track (lat/lon) for one full orbital period centered on now |
| GET    | `/satellites/{norad_id}/next-visible-pass` | Next naked-eye-visible pass over an observer's `latitude`/`longitude` (query params), or `null` if none within `search_days` |
| GET    | `/geocode`               | Resolves a free-text place (`query`, e.g. `"Rosario, Santa Fe, Argentina"`) to a list of candidate `latitude`/`longitude` matches |
| WS     | `/ws/positions`          | Streams the full position list every 2 seconds              |

`next-visible-pass` needs a real "is it dark, is the satellite sunlit" check
against the sun's position, so the backend downloads a small JPL ephemeris
(`de421.bsp`, ~17MB) from the network the first time that endpoint is hit,
and caches it on disk afterwards.

`/geocode` proxies [Nominatim](https://nominatim.openstreetmap.org) (OpenStreetMap),
so it needs outbound internet access and is subject to Nominatim's public
usage policy (no bursts, identifiable `User-Agent` — see
`nominatim_user_agent` in `backend/app/config.py`). The `VisiblePassPanel`
frontend component uses it to let users search by city/province/country
instead of typing raw coordinates.

Example `GET /satellites/positions` response:

```json
[
  {
    "norad_id": 25544,
    "name": "ISS (ZARYA)",
    "latitude": -12.34,
    "longitude": 45.67,
    "altitude_km": 408.2,
    "velocity_km_s": 7.66,
    "timestamp": "2026-08-17T12:00:00Z"
  }
]
```

## Tests

**Backend** (pytest + httpx, against an in-memory SQLite — no need to have Postgres running):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
```

Covers: SGP4 propagation, ground-track sampling and visible-pass prediction (`propagation.py`), TLE fetch/upsert against a mocked Celestrak via `respx` (`tle_fetcher.py`), every REST endpoint under `/satellites`, and the `/ws/positions` WebSocket.

**Frontend** (Vitest + Testing Library, jsdom):

```bash
cd frontend
npm install
npm test          # single run
npm run test:watch # watch mode
```

Covers the `useSatelliteSocket`/`useGroundTrack` hooks, the `App`/`Globe`/`VisiblePassPanel` components (Cesium/Resium are mocked: jsdom has no WebGL).

## Linters

**Backend** — [Ruff](https://docs.astral.sh/ruff/) (lint + format), configured in `backend/pyproject.toml`:

```bash
cd backend
source .venv/bin/activate
ruff check .           # lint
ruff check . --fix     # lint, autofixing what it can
ruff format .          # format
ruff format --check .  # format, only checking
```

**Frontend** — [ESLint](https://eslint.org/) (flat config), configured in `frontend/eslint.config.js`:

```bash
cd frontend
npm run lint       # check
npm run lint:fix   # check, autofixing what it can
```

## Pre-commit hooks

Configured in `.pre-commit-config.yaml` at the repo root. On every `git commit`
it runs, for whichever side(s) of the repo have staged changes: a few generic
hygiene checks (trailing whitespace, merge conflict markers, large files),
the backend linter/formatter (Ruff, autofixing), the backend unit tests, a
backend build sanity check (`compileall`, catches import/syntax errors fast
without needing Docker), the frontend linter (ESLint), the frontend unit
tests (Vitest), and the frontend production build (`vite build`).

The hooks call the tools already installed in `backend/.venv` and
`frontend/node_modules` (see [Tests](#tests) above for how to set those up)
— they don't manage their own Python/Node environment for the project code.

```bash
pip install pre-commit
pre-commit install        # one-time, wires it into .git/hooks/pre-commit

pre-commit run --all-files  # optional: run it on demand, without committing
```

## CI

`.github/workflows/ci.yml` runs the same checks as the pre-commit hooks on
every push to any branch, in two independent jobs (`backend`, `frontend`).
The one difference from the local hooks: instead of the lighter local build
checks, CI builds each service's actual Docker image (`docker build`) as its
final step, since GitHub-hosted runners always have Docker available.

## Configuration

Environment variables (see `.env.example`):

| Variable            | Description                                                          | Default |
|----------------------|-----------------------------------------------------------------------|---------|
| `POSTGRES_USER`      | Postgres username                                                     | `satuser` |
| `POSTGRES_PASSWORD`  | Postgres password                                                     | `satpass` |
| `POSTGRES_DB`        | Postgres database name                                                | `satellites` |
| `CESIUM_ION_TOKEN`   | Cesium ion access token (optional, recommended)                       | *(demo token)* |

Additional backend settings live in `backend/app/config.py`, notably:

- `celestrak_url` — which Celestrak TLE group/satellite to track (default:
  the ISS only, `CATNR=25544`). See the full list of groups at
  [celestrak.org/NORAD/elements](https://celestrak.org/NORAD/elements/).
- `tle_refresh_minutes` — how often TLEs are refreshed (default: 120).

## Roadmap

- [ ] **Migrations** — replace the `create_all` call in the lifespan with Alembic
- [ ] **Historical data** — store position time series with TimescaleDB instead of always recomputing live
- [ ] **More satellites** — track other Celestrak groups (`active`, `visual`, `gps-ops`, ...)
- [x] **Visible passes** — `GET /satellites/{norad_id}/next-visible-pass?latitude=...&longitude=...` (see [API Reference](#api-reference) above)
- [ ] **Authentication** — if the project moves beyond public read-only access
- [x] **Tests** — pytest + httpx for the backend, Vitest/Testing Library for the frontend (see [Tests](#tests) above)
- [x] **Linters, pre-commit hooks & CI** — Ruff (backend) + ESLint (frontend), wired into `.pre-commit-config.yaml` and `.github/workflows/ci.yml` (see [Linters](#linters), [Pre-commit hooks](#pre-commit-hooks) and [CI](#ci) above)

## License

MIT — see [LICENSE](LICENSE).
