export interface SatellitePosition {
  norad_id: number
  name: string
  latitude: number
  longitude: number
  altitude_km: number
  velocity_km_s: number
  timestamp: string
}

export interface PositionsMessage {
  satellites: SatellitePosition[]
}

export interface GroundTrackPoint {
  latitude: number
  longitude: number
  timestamp: string
}
