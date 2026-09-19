import { MapContainer, Marker, TileLayer, Tooltip } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface Props {
  latitude: number
  longitude: number
  locationName: string
}

const incidentIcon = L.divIcon({
  html: '<div style="font-size:22px;line-height:1">🔴</div>',
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

export function IncidentLocationMap({ latitude, longitude, locationName }: Props) {
  const center: [number, number] = [latitude, longitude]
  return (
    <div className="incident-location-map">
      <MapContainer center={center} zoom={13} className="h-full w-full rounded-lg" style={{ minHeight: '280px' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={center} icon={incidentIcon}>
          <Tooltip>{locationName}</Tooltip>
        </Marker>
      </MapContainer>
    </div>
  )
}
