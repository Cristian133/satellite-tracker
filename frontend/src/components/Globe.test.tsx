import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { GroundTrackPoint, SatellitePosition } from '../types/satellite'

// Cesium/Resium need a real WebGL canvas, which jsdom can't provide, so the
// globe rendering itself is out of scope here. These mocks let us verify the
// logic Globe.tsx owns on top of them: which entities render, and when the
// camera flies to a new position. vi.mock calls are hoisted above imports by
// vitest, so Globe.tsx picks up these mocks even though the import below
// comes first in the file.
const flyToMock = vi.fn()

vi.mock('resium', () => ({
  Viewer: ({ children }: { children?: ReactNode }) => <div data-testid="viewer">{children}</div>,
  Entity: ({ name, children }: { name?: string; children?: ReactNode }) => (
    <div data-testid="entity" data-name={name}>
      {children}
    </div>
  ),
  PointGraphics: () => null,
  LabelGraphics: ({ text }: { text: string }) => <div data-testid="label">{text}</div>,
  PolylineGraphics: ({ positions }: { positions: unknown[] }) => (
    <div data-testid="ground-track" data-points={positions.length} />
  ),
  useCesium: () => ({ viewer: { camera: { flyTo: flyToMock } } }),
}))

vi.mock('cesium', () => ({
  Cartesian2: class {
    constructor(
      public x: number,
      public y: number,
    ) {}
  },
  Cartesian3: {
    fromDegrees: vi.fn((longitude: number, latitude: number, height: number) => ({ longitude, latitude, height })),
    // Espeja el comportamiento real: un par [lon, lat] por punto de la traza.
    fromDegreesArray: vi.fn((coords: number[]) => {
      const points: { longitude: number; latitude: number }[] = []
      for (let i = 0; i < coords.length; i += 2) {
        points.push({ longitude: coords[i], latitude: coords[i + 1] })
      }
      return points
    }),
  },
  Color: { YELLOW: 'YELLOW', BLACK: 'BLACK', WHITE: 'WHITE', CYAN: 'CYAN' },
}))

import { Globe } from './Globe'

const satellite: SatellitePosition = {
  norad_id: 25544,
  name: 'ISS (ZARYA)',
  latitude: 12.3,
  longitude: 45.6,
  altitude_km: 408,
  velocity_km_s: 7.66,
  timestamp: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  flyToMock.mockClear()
})

describe('Globe', () => {
  it('renders no satellite entity while no position is available yet', () => {
    render(<Globe satellite={null} />)

    expect(screen.queryByTestId('entity')).not.toBeInTheDocument()
  })

  it('renders an entity labeled with the satellite name once a position arrives', () => {
    render(<Globe satellite={satellite} />)

    expect(screen.getByTestId('entity')).toHaveAttribute('data-name', satellite.name)
    expect(screen.getByTestId('label')).toHaveTextContent(satellite.name)
  })

  it('flies the camera to the satellite the first time a position arrives', () => {
    const { rerender } = render(<Globe satellite={null} />)
    expect(flyToMock).not.toHaveBeenCalled()

    rerender(<Globe satellite={satellite} />)

    expect(flyToMock).toHaveBeenCalledTimes(1)
  })

  it('does not fly the camera again on later position updates', () => {
    const { rerender } = render(<Globe satellite={satellite} />)
    expect(flyToMock).toHaveBeenCalledTimes(1)

    rerender(<Globe satellite={{ ...satellite, latitude: satellite.latitude + 1 }} />)

    expect(flyToMock).toHaveBeenCalledTimes(1)
  })

  it('does not render a ground track when no points are available', () => {
    render(<Globe satellite={satellite} groundTrack={[]} />)

    expect(screen.queryByTestId('ground-track')).not.toBeInTheDocument()
  })

  it('does not render a ground track with a single point (nothing to draw a line between)', () => {
    const track: GroundTrackPoint[] = [{ latitude: 1, longitude: 2, timestamp: '2026-01-01T00:00:00Z' }]

    render(<Globe satellite={satellite} groundTrack={track} />)

    expect(screen.queryByTestId('ground-track')).not.toBeInTheDocument()
  })

  it('renders a polyline with every ground track point once there are at least two', () => {
    const track: GroundTrackPoint[] = [
      { latitude: 1, longitude: 2, timestamp: '2026-01-01T00:00:00Z' },
      { latitude: 3, longitude: 4, timestamp: '2026-01-01T00:01:00Z' },
      { latitude: 5, longitude: 6, timestamp: '2026-01-01T00:02:00Z' },
    ]

    render(<Globe satellite={satellite} groundTrack={track} />)

    expect(screen.getByTestId('ground-track')).toHaveAttribute('data-points', String(track.length))
  })
})
