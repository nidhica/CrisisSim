import { Polygon, Tooltip } from 'react-leaflet'
import type { Zone, ZoneResult } from '../../types'
import {
  formatZoneMapTooltipLines,
  getZoneRiskMapVisual,
  type ZoneRiskLevel,
} from '../../utils/zoneRiskMapVisual'

interface Props {
  zones: Zone[]
  zoneResults: ZoneResult[]
  onZoneClick: (zoneId: string) => void
  selectedZoneId: string | null
}

export function ZoneLayer({ zones, zoneResults, onZoneClick, selectedZoneId }: Props) {
  return (
    <>
      {zones.map(zone => {
        const result = zoneResults.find(r => r.zone_id === zone.zone_id)
        const level: ZoneRiskLevel | undefined = result?.risk_level
        const visual = getZoneRiskMapVisual(level)
        const isSelected = zone.zone_id === selectedZoneId
        const { title, riskLine } = formatZoneMapTooltipLines(
          zone.name,
          level,
          result?.risk_score ?? null,
        )

        return (
          <Polygon
            key={zone.zone_id}
            positions={zone.coordinates as [number, number][]}
            pathOptions={{
              color: isSelected ? '#2563eb' : visual.strokeColor,
              fillColor: visual.fillColor,
              fillOpacity: visual.fillOpacity,
              opacity: isSelected ? 1 : visual.strokeOpacity,
              weight: isSelected ? 3 : visual.strokeWeight,
            }}
            eventHandlers={{ click: () => onZoneClick(zone.zone_id) }}
          >
            <Tooltip className="zone-risk-tooltip">
              <div className="zone-risk-tooltip-inner">
                <div className="zone-risk-tooltip-title">{title}</div>
                <div className="zone-risk-tooltip-risk" style={{ color: visual.fillColor }}>
                  {riskLine}
                </div>
              </div>
            </Tooltip>
          </Polygon>
        )
      })}
    </>
  )
}
