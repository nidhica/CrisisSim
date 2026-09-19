import { Fragment } from 'react'
import { Marker, Tooltip } from 'react-leaflet'
import L from 'leaflet'
import type { Zone } from '../../types'

interface Props { zones: Zone[] }

function makeIcon(emoji: string) {
  return L.divIcon({
    html: `<div style="font-size:18px;line-height:1">${emoji}</div>`,
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

const rescueIcon = makeIcon('🚒')
const ambuIcon = makeIcon('🚑')

export function ResourceMarkers({ zones }: Props) {
  return (
    <>
      {zones.map(zone => {
        const [lat, lng] = zone.centroid
        return (
          <Fragment key={zone.zone_id}>
            {zone.rescue_teams > 0 && (
              <Marker position={[lat + 0.001, lng - 0.001]} icon={rescueIcon}>
                <Tooltip>{zone.name}: {zone.rescue_teams} rescue team(s)</Tooltip>
              </Marker>
            )}
            {zone.ambulances > 0 && (
              <Marker position={[lat - 0.001, lng + 0.001]} icon={ambuIcon}>
                <Tooltip>{zone.name}: {zone.ambulances} ambulance(s)</Tooltip>
              </Marker>
            )}
          </Fragment>
        )
      })}
    </>
  )
}
