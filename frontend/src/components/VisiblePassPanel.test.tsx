import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { VisiblePassPanel } from './VisiblePassPanel'

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return { ok, status, json: async () => body } as Response
}

function fillAndSubmit(latitude: string, longitude: string) {
  fireEvent.change(screen.getByPlaceholderText('Latitud'), { target: { value: latitude } })
  fireEvent.change(screen.getByPlaceholderText('Longitud'), { target: { value: longitude } })
  fireEvent.click(screen.getByRole('button', { name: /buscar/i }))
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('VisiblePassPanel', () => {
  it('disables the search button while there is no norad_id', () => {
    render(<VisiblePassPanel noradId={null} />)

    expect(screen.getByRole('button', { name: /buscar/i })).toBeDisabled()
  })

  it('requests the next visible pass with the entered coordinates', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        rise_time: '2026-01-01T00:00:00Z',
        culminate_time: '2026-01-01T00:02:00Z',
        set_time: '2026-01-01T00:04:00Z',
        max_elevation_deg: 42,
        azimuth_deg: 180,
        weather: null,
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    render(<VisiblePassPanel noradId={25544} />)
    fillAndSubmit('40.7', '-74')

    await waitFor(() => expect(screen.getByText(/Elevación máx\.: 42°/)).toBeInTheDocument())
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/satellites/25544/next-visible-pass?latitude=40.7&longitude=-74',
    )
    expect(screen.getByText(/Azimut: 180°/)).toBeInTheDocument()
    expect(screen.getByText('Sin pronóstico disponible para esa fecha.')).toBeInTheDocument()
  })

  it('shows the weather forecast for the pass time when available', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        rise_time: '2026-01-01T00:00:00Z',
        culminate_time: '2026-01-01T00:02:00Z',
        set_time: '2026-01-01T00:04:00Z',
        max_elevation_deg: 42,
        azimuth_deg: 180,
        weather: {
          timestamp: '2026-01-01T00:00:00Z',
          temperature_c: 18.4,
          cloud_cover_pct: 20,
          precipitation_probability_pct: 5,
          description: 'Despejado',
        },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    render(<VisiblePassPanel noradId={25544} />)
    fillAndSubmit('40.7', '-74')

    await waitFor(() => expect(screen.getByText(/Despejado/)).toBeInTheDocument())
    expect(screen.getByText('Temperatura: 18°C')).toBeInTheDocument()
    expect(screen.getByText('Nubosidad: 20%')).toBeInTheDocument()
    expect(screen.getByText(/Prob\. de precipitación: 5%/)).toBeInTheDocument()
  })

  it('shows a message when no visible pass is found', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(null))
    vi.stubGlobal('fetch', fetchMock)

    render(<VisiblePassPanel noradId={25544} />)
    fillAndSubmit('40.7', '-74')

    await waitFor(() =>
      expect(screen.getByText('Ningún pase visible en los próximos 10 días.')).toBeInTheDocument(),
    )
  })

  it('shows an error message when the server responds with an error status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(null, false, 404))
    vi.stubGlobal('fetch', fetchMock)

    render(<VisiblePassPanel noradId={25544} />)
    fillAndSubmit('40.7', '-74')

    await waitFor(() =>
      expect(screen.getByText('El servidor respondió 404.')).toBeInTheDocument(),
    )
  })

  it('shows an error message when the request itself fails', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'))
    vi.stubGlobal('fetch', fetchMock)

    render(<VisiblePassPanel noradId={25544} />)
    fillAndSubmit('40.7', '-74')

    await waitFor(() =>
      expect(screen.getByText('No se pudo conectar con el servidor.')).toBeInTheDocument(),
    )
  })
})
