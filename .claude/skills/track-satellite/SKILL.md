---
name: track-satellite
description: Guía para agregar o cambiar qué satélite(s) trackea el backend (hoy solo trackea la ISS, CATNR=25544). Usar cuando el usuario pide sumar un satélite nuevo, trackear un grupo de Celestrak (estaciones, Starlink, clima, etc.), busca un satélite por nombre/NORAD ID, o pregunta por qué no aparece cierto satélite en la app / por qué la UI solo muestra uno.
---

# Agregar o cambiar el/los satélite(s) trackeado(s)

## Qué controla esto

Todo pasa por un solo valor: `celestrak_url` en
`backend/app/config.py`. Es la URL que `fetch_and_store_tles`
(`backend/app/tle_fetcher.py`) descarga y parsea — hace upsert de **cada**
grupo de 3 líneas (nombre + línea1 + línea2) que venga en la respuesta como
una fila en la tabla `Satellite`. El fetcher **ya soporta múltiples
satélites** (está testeado en `backend/tests/test_tle_fetcher.py` con 2
satélites), el límite hoy es que la URL default solo pide uno (`CATNR=25544`
= ISS).

## Sintaxis de Celestrak (`gp.php`)

Catálogo completo navegable en https://celestrak.org/NORAD/elements/. Los
parámetros de query más útiles:

- `CATNR=<norad_id>` — un solo satélite puntual (ej. `25544` = ISS).
- `GROUP=<nombre>` — un grupo entero predefinido, ej. `stations` (ISS +
  Tiangong/CSS), `starlink`, `weather`, `gps-ops`, `noaa`, `science`, etc.
  Lista completa de grupos en esa misma página.
- `NAME=<texto>` — búsqueda por nombre.
- `FORMAT=tle` — dejarlo siempre así, es el formato que parsea el fetcher.

⚠️ Celestrak **no soporta una lista de `CATNR` separada por comas**. Si
querés un conjunto de satélites puntuales que no coincide con ningún
`GROUP` existente, no hay una sola URL que los traiga juntos — hay que
extender `fetch_and_store_tles` para que itere sobre varias URLs/parámetros
(fuera del alcance de este cambio simple; avisar al usuario si es lo que
necesita).

## Pasos

1. **Elegí el `CATNR` o `GROUP`** que corresponde (buscar el satélite en
   celestrak.org o pedirle el NORAD ID al usuario si no lo tiene).

2. **Aplicá el cambio, de preferencia sin tocar código**: seteando
   `CELESTRAK_URL` en `.env` (pydantic-settings lee env vars en mayúsculas
   para los campos de `Settings`, no hace falta `.env.example` porque es
   local). Ejemplo para trackear todas las estaciones:

   ```
   CELESTRAK_URL=https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle
   ```

   Si el cambio es para que quede como default del proyecto (no solo
   local), se edita el valor default de `celestrak_url` en
   `backend/app/config.py` — en ese caso es un cambio de código versionado,
   así que si hace falta comitearlo aplica la skill `git-ask-first`: pedir
   confirmación antes de correr el commit.

3. **Reiniciá el backend** para que relea la config — `settings = Settings()`
   se instancia una sola vez al importar el módulo, así que un simple
   refresh de TLEs no alcanza:

   ```
   docker compose restart backend
   ```

4. **Forzá el primer refresh** (si no querés esperar a `tle_refresh_minutes`,
   default 120 min):

   ```
   curl -X POST http://localhost:8000/satellites/refresh
   ```

5. **Verificá** que entraron todos: `curl http://localhost:8000/satellites`
   debería listar un `Satellite` por cada TLE del set nuevo.

## ⚠️ Antes de dar esto por terminado: el frontend solo muestra UNO

`frontend/src/hooks/useSatelliteSocket.ts` toma `data.satellites[0]` del
mensaje del WebSocket y descarta el resto — está escrito asumiendo que solo
hay un satélite trackeado (hay un comentario explícito ahí mismo: *"Por
ahora el backend trackea un solo satélite..."*). Si el pedido era sumar un
satélite **más** para verlo en el globo junto al resto, el backend ya lo
sirve bien pero **la UI lo va a ignorar** hasta modificar:

- `useSatelliteSocket.ts` — manejar un array en vez de un solo objeto.
- `App.tsx` — pasar la lista completa en vez de `satellite?.norad_id`.
- La capa de Cesium que dibuja la entidad del satélite — instanciar una por
  cada uno.

Avisar esto al usuario y ofrecer hacer ese trabajo aparte si lo necesita —
no asumir que cambiar `celestrak_url` solo ya resuelve "quiero ver el
satélite X en el mapa" si ya hay otro trackeado.

## Chequeo final

- `cd backend && python -m pytest` sigue pasando (el fetcher está testeado
  con datos de muestra fijos en `tests/sample_data.py`, no le importa qué
  URL real esté configurada).
- Si el satélite nuevo queda como default del proyecto, considerar agregar
  su caso a `tests/sample_data.py` / `test_tle_fetcher.py`.
