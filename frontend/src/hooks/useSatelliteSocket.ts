import { useEffect, useRef, useState } from 'react'
import type { PositionsMessage, SatellitePosition } from '../types/satellite'

const WS_URL =
  (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/^http/, 'ws') +
  '/ws/positions'

/** Por ahora el backend trackea un solo satélite (la ISS), así que nos
 * quedamos con el primer elemento del array que manda el WebSocket. */
export function useSatelliteSocket() {
  const [satellite, setSatellite] = useState<SatellitePosition | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let cancelled = false

    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => !cancelled && setConnected(true)
      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        setTimeout(connect, 2000) // reintento simple
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (event) => {
        const data: PositionsMessage = JSON.parse(event.data)
        if (!cancelled) setSatellite(data.satellites[0] ?? null)
      }
    }

    connect()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [])

  return { satellite, connected }
}
