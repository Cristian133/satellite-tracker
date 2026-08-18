import { useEffect, useState } from 'react'
import type { GroundTrackPoint } from '../types/satellite'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// La forma de la órbita cambia lento (el backend recalcula la ventana
// centrada en "ahora" en cada request); no hace falta pedirla más seguido
// que esto.
const REFRESH_INTERVAL_MS = 5 * 60 * 1000

/** Trae la traza de órbita (ground track) de un satélite y la refresca
 * periódicamente. Devuelve [] mientras no hay norad_id o mientras no llegó
 * la primera respuesta. */
export function useGroundTrack(noradId: number | null): GroundTrackPoint[] {
  const [track, setTrack] = useState<GroundTrackPoint[]>([])

  // Reinicia la traza al cambiar de satélite ajustando el estado durante el
  // render (en vez de en un efecto): evita el render en cascada que dispara
  // un setState síncrono dentro de un efecto.
  // https://react.dev/reference/react/useState#storing-information-from-previous-renders
  const [trackedNoradId, setTrackedNoradId] = useState(noradId)
  if (noradId !== trackedNoradId) {
    setTrackedNoradId(noradId)
    setTrack([])
  }

  useEffect(() => {
    if (noradId === null) return

    let cancelled = false

    async function fetchTrack() {
      try {
        const res = await fetch(`${API_URL}/satellites/${noradId}/ground-track`)
        if (!res.ok) return
        const data: GroundTrackPoint[] = await res.json()
        if (!cancelled) setTrack(data)
      } catch {
        // Se reintenta en el próximo tick; no vale la pena romper la UI por
        // un fetch que falló.
      }
    }

    fetchTrack()
    const interval = setInterval(fetchTrack, REFRESH_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [noradId])

  return track
}
