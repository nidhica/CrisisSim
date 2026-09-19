import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { Scenario, ZoneResult, SimulationResult } from '../../types'
import { ZoneLayer } from './ZoneLayer'
import { ResourceMarkers } from './ResourceMarkers'
import { FacilityMarkers } from './FacilityMarkers'
import { ZoneDetailPanel } from './ZoneDetailPanel'
import { SimMapLegend } from './SimMapLegend'
import { Marker, Tooltip } from 'react-leaflet'
import L from 'leaflet'

interface Props {
  scenario: Scenario
  zoneResults: ZoneResult[]
  result: SimulationResult | null
  incidentPin?: { latitude: number; longitude: number; label: string }
}

const citizenIncidentIcon = L.divIcon({
  html: '<div style="font-size:22px;line-height:1">📍</div>',
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

function resolveMapCenter(scenario: Scenario): [number, number] {
  if (scenario.latitude != null && scenario.longitude != null) {
    return [scenario.latitude, scenario.longitude]
  }
  if (scenario.zones.length > 0) {
    return [scenario.zones[0].centroid[0], scenario.zones[0].centroid[1]]
  }
  return [51.505, -0.09]
}

function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, map.getZoom() || 14)
  }, [center, map])
  return null
}

export function SimMap({ scenario, zoneResults, result: _result, incidentPin }: Props) {
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null)
  const center = useMemo(() => resolveMapCenter(scenario), [scenario])
  const mapKey = `${scenario.scenario_id}-${center[0].toFixed(5)}-${center[1].toFixed(5)}`

  const selectedZone = scenario.zones.find(z => z.zone_id === selectedZoneId)
  const selectedResult = zoneResults.find(r => r.zone_id === selectedZoneId)

  return (
    <div className="relative h-full">
      <MapContainer
        key={mapKey}
        center={center}
        zoom={14}
        className="h-full w-full rounded-lg ops-map-canvas"
        style={{ minHeight: '400px', borderRadius: '8px' }}
      >
        <MapRecenter center={center} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoneLayer
          zones={scenario.zones}
          zoneResults={zoneResults}
          onZoneClick={setSelectedZoneId}
          selectedZoneId={selectedZoneId}
        />
        <ResourceMarkers zones={scenario.zones} />
        <FacilityMarkers shelters={scenario.shelters} hospitals={scenario.hospitals} />
        {incidentPin && (
          <Marker
            position={[incidentPin.latitude, incidentPin.longitude]}
            icon={citizenIncidentIcon}
          >
            <Tooltip>Citizen report: {incidentPin.label}</Tooltip>
          </Marker>
        )}
      </MapContainer>

      <SimMapLegend showCitizenPin={Boolean(incidentPin)} />

      {selectedZone && selectedResult && (
        <ZoneDetailPanel
          zone={selectedZone}
          result={selectedResult}
          hazardType={scenario.hazard_type}
          onClose={() => setSelectedZoneId(null)}
        />
      )}
    </div>
  )
}
