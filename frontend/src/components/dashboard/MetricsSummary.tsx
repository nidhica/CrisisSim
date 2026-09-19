import type { HazardType, Scenario, SimulationResult } from '../../types'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  scenario: Scenario
  result: SimulationResult | null
  isRunning: boolean
}

const HAZARD_LABELS: Record<HazardType, string> = {
  flood: 'Flood',
  fire: 'Fire',
  earthquake: 'Earthquake',
  cyclone: 'Cyclone / Severe Storm',
  industrial_accident: 'Industrial Accident',
}

export function MetricsSummary({ scenario, result, isRunning }: Props) {
  const hazard = (result?.hazard_type || scenario.hazard_type || 'flood') as HazardType
  const totalPop = scenario.zones.reduce((s, z) => s + z.affected_population, 0)
  const totalRescue = scenario.zones.reduce((s, z) => s + z.rescue_teams, 0)
  const totalAmbu = scenario.zones.reduce((s, z) => s + z.ambulances, 0)
  const shelterCap = scenario.shelters.reduce((s, sh) => s + sh.capacity, 0)
  const shelterOcc = scenario.shelters.reduce((s, sh) => s + sh.current_occupancy, 0)
  const hospCap = scenario.hospitals.reduce((s, h) => s + h.capacity + h.surge_capacity, 0)
  const hospOcc = scenario.hospitals.reduce((s, h) => s + h.current_occupancy, 0)
  const specialistTotal = scenario.zones.reduce((sum, zone) => {
    return sum + Object.values(zone.specialist_resources || {}).reduce((a, b) => a + b, 0)
  }, 0)

  const avgRisk = result
    ? result.baseline_zone_results.reduce((s, z) => s + z.risk_score, 0) /
      result.baseline_zone_results.length
    : null
  const avgRT = result
    ? result.baseline_zone_results.reduce((s, z) => s + z.response_time_minutes, 0) /
      result.baseline_zone_results.length
    : null

  const cards = [
    { label: 'Active hazard', value: HAZARD_LABELS[hazard], large: false },
    { label: 'Population at risk', value: totalPop.toLocaleString(), large: true },
    ...(hazard === 'flood'
      ? [
          { label: 'Rescue teams', value: String(totalRescue), large: true },
          { label: 'Ambulances', value: String(totalAmbu), large: true },
        ]
      : [{ label: 'Specialist units', value: String(specialistTotal), large: true }]),
    {
      label: 'Shelter utilisation',
      value: `${shelterOcc} / ${shelterCap}`,
      large: false,
      warn: shelterOcc > shelterCap,
    },
    {
      label: 'Hospital utilisation',
      value: `${hospOcc} / ${hospCap}`,
      large: false,
      warn: hospOcc > hospCap,
    },
    {
      label: 'Average risk',
      value: isRunning ? null : avgRisk != null ? avgRisk.toFixed(1) : '—',
      large: true,
    },
    {
      label: 'Response time',
      value: isRunning ? null : avgRT != null ? `${avgRT.toFixed(1)} min` : '—',
      large: true,
    },
  ]

  return (
    <div className="ops-metric-sidebar">
      {cards.map(card => (
        <div
          key={card.label}
          className={`ops-sidebar-metric${card.warn ? ' ops-sidebar-metric-warn' : ''}`}
        >
          <p className="ops-metric-value" style={card.large ? undefined : { fontSize: '16px' }}>
            {card.value === null ? <LoadingSpinner label="" /> : card.value}
          </p>
          <p className="ops-metric-label">{card.label}</p>
        </div>
      ))}
    </div>
  )
}
