import {
  ZONE_RISK_LEGEND_LEVELS,
  ZONE_RISK_MAP_VISUAL,
} from '../../utils/zoneRiskMapVisual'

export function SimMapLegend({ showCitizenPin }: { showCitizenPin?: boolean }) {
  return (
    <div className="sim-map-legend" aria-label="Simulation map legend">
      <p className="sim-map-legend-title">SIMULATION MAP</p>
      <ul>
        {ZONE_RISK_LEGEND_LEVELS.map(level => {
          const visual = ZONE_RISK_MAP_VISUAL[level]
          return (
            <li key={level}>
              <span
                className="legend-swatch legend-swatch-lg"
                style={{ backgroundColor: visual.fillColor }}
                aria-hidden
              />
              {visual.legendLabel}
            </li>
          )
        })}
        {showCitizenPin && <li>📍 Citizen report</li>}
        <li>🚑 Response resource</li>
        <li>🏥 Simulated facility</li>
      </ul>
      <p className="sim-map-legend-warning">⚠ Simulated boundaries · prototype assets only</p>
    </div>
  )
}
