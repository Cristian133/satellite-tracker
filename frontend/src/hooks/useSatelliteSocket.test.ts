import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PositionsMessage } from '../types/satellite'
import { useSatelliteSocket } from './useSatelliteSocket'

/** Minimal stand-in for the browser WebSocket, fully controlled by tests. */
class MockWebSocket {
  static instances: MockWebSocket[] = []

  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  closed = false

  constructor(public url: string) {
    MockWebSocket.instances.push(this)
  }

  send() {}

  close() {
    this.closed = true
    this.onclose?.()
  }
}

function latestSocket(): MockWebSocket {
  const socket = MockWebSocket.instances.at(-1)
  if (!socket) throw new Error('no WebSocket was created')
  return socket
}

function samplePosition(overrides: Partial<PositionsMessage['satellites'][number]> = {}) {
  return {
    norad_id: 25544,
    name: 'ISS (ZARYA)',
    latitude: 12.3,
    longitude: 45.6,
    altitude_km: 408,
    velocity_km_s: 7.66,
    timestamp: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  MockWebSocket.instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useSatelliteSocket', () => {
  it('starts disconnected with no satellite position', () => {
    const { result } = renderHook(() => useSatelliteSocket())

    expect(result.current.connected).toBe(false)
    expect(result.current.satellite).toBeNull()
  })

  it('opens a WebSocket connection on mount', () => {
    renderHook(() => useSatelliteSocket())

    expect(MockWebSocket.instances).toHaveLength(1)
  })

  it('marks the connection as established once the socket opens', () => {
    const { result } = renderHook(() => useSatelliteSocket())

    act(() => latestSocket().onopen?.())

    expect(result.current.connected).toBe(true)
  })

  it('stores the first satellite from an incoming position message', () => {
    const { result } = renderHook(() => useSatelliteSocket())
    const position = samplePosition()
    const message: PositionsMessage = { satellites: [position] }

    act(() => latestSocket().onmessage?.({ data: JSON.stringify(message) }))

    expect(result.current.satellite).toEqual(position)
  })

  it('clears the satellite when a message carries an empty list', () => {
    const { result } = renderHook(() => useSatelliteSocket())

    act(() => latestSocket().onmessage?.({ data: JSON.stringify({ satellites: [samplePosition()] }) }))
    expect(result.current.satellite).not.toBeNull()

    act(() => latestSocket().onmessage?.({ data: JSON.stringify({ satellites: [] }) }))
    expect(result.current.satellite).toBeNull()
  })

  it('marks the connection as lost when the socket closes', () => {
    const { result } = renderHook(() => useSatelliteSocket())
    act(() => latestSocket().onopen?.())

    act(() => latestSocket().onclose?.())

    expect(result.current.connected).toBe(false)
  })

  it('reconnects automatically after the socket closes', () => {
    renderHook(() => useSatelliteSocket())
    expect(MockWebSocket.instances).toHaveLength(1)

    act(() => latestSocket().onclose?.())
    act(() => vi.advanceTimersByTime(2000))

    expect(MockWebSocket.instances).toHaveLength(2)
  })

  it('closes the socket on unmount and does not reconnect afterwards', () => {
    const { unmount } = renderHook(() => useSatelliteSocket())
    const socket = latestSocket()

    unmount()

    expect(socket.closed).toBe(true)
    act(() => vi.advanceTimersByTime(5000))
    expect(MockWebSocket.instances).toHaveLength(1)
  })
})
