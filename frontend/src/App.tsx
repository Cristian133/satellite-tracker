import { Ion } from 'cesium'
import './App.css'
import { Globe } from './components/Globe'
import { VisiblePassPanel } from './components/VisiblePassPanel'
import { useGroundTrack } from './hooks/useGroundTrack'
import { useSatelliteSocket } from './hooks/useSatelliteSocket'

const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN
if (ionToken) {
  Ion.defaultAccessToken = ionToken
}

function App() {
  const { satellite, connected } = useSatelliteSocket()
  const groundTrack = useGroundTrack(satellite?.norad_id ?? null)

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <Globe satellite={satellite} groundTrack={groundTrack} />
      <VisiblePassPanel noradId={satellite?.norad_id ?? null} />
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          zIndex: 1000,
          background: 'rgba(0,0,0,0.6)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: 6,
          fontFamily: 'sans-serif',
          fontSize: 13,
        }}
      >
        <div>{connected ? '🟢 Conectado' : '🔴 Reconectando...'}</div>
        <div>
          {satellite
            ? `${satellite.name} — lat ${satellite.latitude.toFixed(2)}° lon ${satellite.longitude.toFixed(2)}° alt ${satellite.altitude_km.toFixed(0)} km`
            : 'Esperando posición...'}
        </div>
      </div>
    </div>
  )
}

export default App
