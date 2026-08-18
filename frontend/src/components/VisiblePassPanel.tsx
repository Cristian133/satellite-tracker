import { useState } from 'react'
import type { GeocodeResult, VisiblePass } from '../types/satellite'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface VisiblePassPanelProps {
  noradId: number | null
}

type SearchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'found'; pass: VisiblePass }
  | { status: 'none' }

type LocationMode = 'coords' | 'place'

type GeocodeState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'results'; results: GeocodeResult[] }

/** Panel para buscar el próximo pase visible a ojo desnudo del satélite
 * trackeado, dada la ubicación del observador. A diferencia de la traza de
 * órbita (que se pide sola apenas hay un satélite), esto es on-demand: el
 * usuario ingresa su ubicación (coordenadas o una ciudad por nombre) y
 * dispara la búsqueda. */
export function VisiblePassPanel({ noradId }: VisiblePassPanelProps) {
  const [mode, setMode] = useState<LocationMode>('coords')

  // Modo coordenadas
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')

  // Modo ciudad/provincia/país
  const [placeQuery, setPlaceQuery] = useState('')
  const [geocodeState, setGeocodeState] = useState<GeocodeState>({ status: 'idle' })
  const [selectedPlace, setSelectedPlace] = useState<GeocodeResult | null>(null)

  const [state, setState] = useState<SearchState>({ status: 'idle' })

  function switchMode(next: LocationMode) {
    setMode(next)
    setState({ status: 'idle' })
  }

  async function handleGeocodeSearch(event: React.FormEvent) {
    event.preventDefault()
    setSelectedPlace(null)
    setGeocodeState({ status: 'loading' })
    try {
      const params = new URLSearchParams({ query: placeQuery })
      const res = await fetch(`${API_URL}/geocode?${params}`)
      if (!res.ok) {
        setGeocodeState({ status: 'error', message: `El servidor respondió ${res.status}.` })
        return
      }
      const results: GeocodeResult[] = await res.json()
      if (results.length === 0) {
        setGeocodeState({ status: 'error', message: 'No se encontró ese lugar.' })
        return
      }
      setGeocodeState({ status: 'results', results })
    } catch {
      setGeocodeState({ status: 'error', message: 'No se pudo conectar con el servidor.' })
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (noradId === null) return

    let lat: number
    let lon: number
    if (mode === 'coords') {
      lat = Number(latitude)
      lon = Number(longitude)
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        setState({ status: 'error', message: 'Latitud y longitud tienen que ser números.' })
        return
      }
    } else {
      if (!selectedPlace) {
        setState({ status: 'error', message: 'Elegí un lugar de la lista primero.' })
        return
      }
      lat = selectedPlace.latitude
      lon = selectedPlace.longitude
    }

    setState({ status: 'loading' })
    try {
      const params = new URLSearchParams({
        latitude: String(lat),
        longitude: String(lon),
      })
      const res = await fetch(`${API_URL}/satellites/${noradId}/next-visible-pass?${params}`)
      if (!res.ok) {
        setState({ status: 'error', message: `El servidor respondió ${res.status}.` })
        return
      }
      const pass: VisiblePass | null = await res.json()
      setState(pass ? { status: 'found', pass } : { status: 'none' })
    } catch {
      setState({ status: 'error', message: 'No se pudo conectar con el servidor.' })
    }
  }

  const canSubmit =
    noradId !== null &&
    state.status !== 'loading' &&
    (mode === 'coords' || selectedPlace !== null)

  return (
    <div
      style={{
        position: 'absolute',
        top: 80,
        left: 10,
        zIndex: 1000,
        background: 'rgba(0,0,0,0.6)',
        color: 'white',
        padding: '8px 12px',
        borderRadius: 6,
        fontFamily: 'sans-serif',
        fontSize: 13,
        width: 240,
      }}
    >
      <div style={{ marginBottom: 6 }}>🔭 Próximo pase visible</div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        <button
          type="button"
          onClick={() => switchMode('coords')}
          disabled={mode === 'coords'}
          style={{ flex: 1 }}
        >
          Coordenadas
        </button>
        <button
          type="button"
          onClick={() => switchMode('place')}
          disabled={mode === 'place'}
          style={{ flex: 1 }}
        >
          Ciudad
        </button>
      </div>

      {mode === 'coords' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <input
            type="number"
            step="any"
            placeholder="Latitud"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            required
            style={{ padding: 4 }}
          />
          <input
            type="number"
            step="any"
            placeholder="Longitud"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            required
            style={{ padding: 4 }}
          />
        </div>
      )}

      {mode === 'place' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <form onSubmit={handleGeocodeSearch} style={{ display: 'flex', gap: 4 }}>
            <input
              type="text"
              placeholder="Ciudad, provincia, país"
              value={placeQuery}
              onChange={(e) => setPlaceQuery(e.target.value)}
              required
              style={{ padding: 4, flex: 1, minWidth: 0 }}
            />
            <button type="submit" disabled={geocodeState.status === 'loading'}>
              {geocodeState.status === 'loading' ? '...' : 'Buscar'}
            </button>
          </form>

          {geocodeState.status === 'error' && (
            <div style={{ color: '#ff8080' }}>{geocodeState.message}</div>
          )}

          {geocodeState.status === 'results' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 120, overflowY: 'auto' }}>
              {geocodeState.results.map((place, i) => (
                <label
                  key={i}
                  style={{
                    display: 'flex',
                    gap: 4,
                    alignItems: 'flex-start',
                    cursor: 'pointer',
                    background:
                      selectedPlace?.display_name === place.display_name
                        ? 'rgba(255,255,255,0.15)'
                        : 'transparent',
                    padding: 2,
                    borderRadius: 3,
                  }}
                >
                  <input
                    type="radio"
                    name="place"
                    checked={selectedPlace?.display_name === place.display_name}
                    onChange={() => setSelectedPlace(place)}
                    style={{ marginTop: 2 }}
                  />
                  <span>{place.display_name}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: 6 }}>
        <button type="submit" disabled={!canSubmit} style={{ width: '100%' }}>
          {state.status === 'loading' ? 'Buscando...' : 'Buscar pase'}
        </button>
      </form>

      {state.status === 'error' && (
        <div style={{ marginTop: 6, color: '#ff8080' }}>{state.message}</div>
      )}
      {state.status === 'none' && (
        <div style={{ marginTop: 6 }}>Ningún pase visible en los próximos 10 días.</div>
      )}
      {state.status === 'found' && (
        <div style={{ marginTop: 6 }}>
          <div>Sale: {new Date(state.pass.rise_time).toLocaleString()}</div>
          <div>Culmina: {new Date(state.pass.culminate_time).toLocaleString()}</div>
          <div>Elevación máx.: {state.pass.max_elevation_deg.toFixed(0)}°</div>
          <div>Azimut: {state.pass.azimuth_deg.toFixed(0)}°</div>

          <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
            {state.pass.weather ? (
              <>
                <div>🌤️ {state.pass.weather.description}</div>
                <div>Temperatura: {state.pass.weather.temperature_c.toFixed(0)}°C</div>
                <div>Nubosidad: {state.pass.weather.cloud_cover_pct.toFixed(0)}%</div>
                <div>
                  Prob. de precipitación:{' '}
                  {state.pass.weather.precipitation_probability_pct.toFixed(0)}%
                </div>
              </>
            ) : (
              <div>Sin pronóstico disponible para esa fecha.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
