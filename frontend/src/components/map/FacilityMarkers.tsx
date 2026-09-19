import { Marker, Tooltip } from 'react-leaflet'
import L from 'leaflet'
import type { Shelter, Hospital } from '../../types'

interface Props { shelters: Shelter[]; hospitals: Hospital[] }

function makeIcon(emoji: string) {
  return L.divIcon({
    html: `<div style="font-size:20px;line-height:1">${emoji}</div>`,
    className: '',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

const shelterIcon = makeIcon('🏠')
const hospitalIcon = makeIcon('🏥')

export function FacilityMarkers({ shelters, hospitals }: Props) {
  return (
    <>
      {shelters.map(s => (
        <Marker key={s.shelter_id} position={s.coordinates as [number, number]} icon={shelterIcon}>
          <Tooltip>{s.name}: {s.current_occupancy}/{s.capacity}</Tooltip>
        </Marker>
      ))}
      {hospitals.map(h => (
        <Marker key={h.hospital_id} position={h.coordinates as [number, number]} icon={hospitalIcon}>
          <Tooltip>{h.name}: {h.current_occupancy}/{h.capacity + h.surge_capacity} (eff. cap)</Tooltip>
        </Marker>
      ))}
    </>
  )
}
