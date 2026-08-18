import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { GroundTrackPoint } from '../types/satellite'
import { useGroundTrack } from './useGroundTrack'

function jsonResponse(body: unknown, ok = true): Response {
  return { ok, json: async () => body } as Response
}

const samplePoints: GroundTrackPoint[] = [
  { latitude: 1, longitude: 2, timestamp: '2026-01-01T00:00:00Z' },
  { latitude: 3, longitude: 4, timestamp: '2026-01-01T00:01:00Z' },
]

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useGroundTrack', () => {
  it('returns an empty track while there is no norad_id', () => {
    const { result } = renderHook(() => useGroundTrack(null))

    expect(result.current).toEqual([])
  })

  it('fetches the ground track for the given norad_id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(samplePoints))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useGroundTrack(25544))

    await waitFor(() => expect(result.current).toEqual(samplePoints))
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/satellites/25544/ground-track')
  })

  it('keeps an empty track when the response is not ok', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(null, false))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useGroundTrack(25544))
    await act(async () => {})

    expect(result.current).toEqual([])
  })

  it('does not crash when the fetch itself fails', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useGroundTrack(25544))
    await act(async () => {})

    expect(result.current).toEqual([])
  })

  it('refetches periodically', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(samplePoints))
    vi.stubGlobal('fetch', fetchMock)

    renderHook(() => useGroundTrack(25544))
    await vi.advanceTimersByTimeAsync(0) // deja resolver el fetch inicial
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(5 * 60 * 1000)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('clears the track and stops fetching once norad_id becomes null', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(samplePoints))
    vi.stubGlobal('fetch', fetchMock)

    const { result, rerender } = renderHook(({ noradId }) => useGroundTrack(noradId), {
      initialProps: { noradId: 25544 as number | null },
    })
    await waitFor(() => expect(result.current).toEqual(samplePoints))

    rerender({ noradId: null })

    expect(result.current).toEqual([])
  })
})
