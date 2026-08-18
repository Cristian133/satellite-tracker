import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { SatellitePosition } from './types/satellite'

const useSatelliteSocketMock = vi.fn()
const useGroundTrackMock = vi.fn()

vi.mock('./hooks/useSatelliteSocket', () => ({
  useSatelliteSocket: () => useSatelliteSocketMock(),
}))

vi.mock('./hooks/useGroundTrack', () => ({
  useGroundTrack: (noradId: number | null) => useGroundTrackMock(noradId),
}))

vi.mock('./components/Globe', () => ({
  Globe: ({ groundTrack }: { groundTrack?: unknown[] }) => (
    <div data-testid="globe" data-track-points={groundTrack?.length ?? 0} />
  ),
}))

vi.mock('cesium', () => ({
  Ion: { defaultAccessToken: '' },
}))

// vi.mock calls above are hoisted above this import by vitest.
import App from './App'

const satellite: SatellitePosition = {
  norad_id: 25544,
  name: 'ISS (ZARYA)',
  latitude: 12.345,
  longitude: -45.678,
  altitude_km: 408.2,
  velocity_km_s: 7.66,
  timestamp: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  useGroundTrackMock.mockReturnValue([])
})

describe('App', () => {
  it('shows a waiting message while no satellite position has arrived', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite: null, connected: false })

    render(<App />)

    expect(screen.getByText('Esperando posición...')).toBeInTheDocument()
  })

  it('shows the reconnecting status when not connected', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite: null, connected: false })

    render(<App />)

    expect(screen.getByText('🔴 Reconectando...')).toBeInTheDocument()
  })

  it('shows the connected status once the socket is open', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite: null, connected: true })

    render(<App />)

    expect(screen.getByText('🟢 Conectado')).toBeInTheDocument()
  })

  it('renders the satellite name and rounded coordinates once a position arrives', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite, connected: true })

    render(<App />)

    expect(
      screen.getByText('ISS (ZARYA) — lat 12.35° lon -45.68° alt 408 km'),
    ).toBeInTheDocument()
  })

  it('renders the Globe', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite: null, connected: false })

    render(<App />)

    expect(screen.getByTestId('globe')).toBeInTheDocument()
  })

  it('requests the ground track for the current satellite norad_id', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite, connected: true })

    render(<App />)

    expect(useGroundTrackMock).toHaveBeenCalledWith(satellite.norad_id)
  })

  it('requests no ground track while there is no satellite yet', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite: null, connected: false })

    render(<App />)

    expect(useGroundTrackMock).toHaveBeenCalledWith(null)
  })

  it('passes the ground track points down to the Globe', () => {
    useSatelliteSocketMock.mockReturnValue({ satellite, connected: true })
    useGroundTrackMock.mockReturnValue([
      { latitude: 1, longitude: 2, timestamp: '2026-01-01T00:00:00Z' },
      { latitude: 3, longitude: 4, timestamp: '2026-01-01T00:01:00Z' },
    ])

    render(<App />)

    expect(screen.getByTestId('globe')).toHaveAttribute('data-track-points', '2')
  })
})
