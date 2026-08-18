import { useEffect, useRef } from 'react'
import { Cartesian2, Cartesian3, Color } from 'cesium'
import { Entity, LabelGraphics, PointGraphics, PolylineGraphics, Viewer, useCesium } from 'resium'
import type { GroundTrackPoint, SatellitePosition } from '../types/satellite'

interface GlobeProps {
  satellite: SatellitePosition | null
  groundTrack?: GroundTrackPoint[]
}

/** Vuela la cámara hacia el satélite la primera vez que llega su posición. */
function CameraTracker({ satellite }: { satellite: SatellitePosition | null }) {
  const { viewer } = useCesium()
  const hasFlown = useRef(false)

  useEffect(() => {
    if (!viewer || !satellite || hasFlown.current) return
    hasFlown.current = true

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(
        satellite.longitude,
        satellite.latitude,
        satellite.altitude_km * 1000 + 3_000_000, // un poco más lejos para ubicar el punto en contexto
      ),
      duration: 2,
    })
  }, [viewer, satellite])

  return null
}

export function Globe({ satellite, groundTrack = [] }: GlobeProps) {
  return (
    <Viewer full timeline={false} animation={false}>
      <CameraTracker satellite={satellite} />
      {groundTrack.length > 1 && (
        <Entity>
          <PolylineGraphics
            positions={Cartesian3.fromDegreesArray(
              groundTrack.flatMap((point) => [point.longitude, point.latitude]),
            )}
            width={2}
            material={Color.CYAN}
          />
        </Entity>
      )}
      {satellite && (
        <Entity
          name={satellite.name}
          position={Cartesian3.fromDegrees(
            satellite.longitude,
            satellite.latitude,
            satellite.altitude_km * 1000,
          )}
        >
          <PointGraphics
            pixelSize={14}
            color={Color.YELLOW}
            outlineColor={Color.BLACK}
            outlineWidth={2}
          />
          <LabelGraphics
            text={satellite.name}
            font="14px sans-serif"
            fillColor={Color.WHITE}
            pixelOffset={new Cartesian2(0, -26)}
          />
        </Entity>
      )}
    </Viewer>
  )
}
