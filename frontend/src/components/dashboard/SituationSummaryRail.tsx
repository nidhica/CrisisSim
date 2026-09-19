import type { HazardType, Scenario, SimulationResult } from '../../types'
import {
  averageBaselineResponseTime,
  averageBaselineRisk,
  primaryBottleneck,
} from '../../utils/commandBriefUtils'

const HAZARD_LABELS: Record<HazardType, string> = {
  flood: 'Flood',
  fire: 'Fire',
  earthquake: 'Earthquake',
  cyclone: 'Cyclone / Severe Storm',
  industrial_accident: 'Industrial Accident',
}

interface Props {
  scenario: Scenario
  result: SimulationResult | null
  isRunning: boolean
}

export function SituationSummaryRail({ scenario, result, isRunning }: Props) {
  const hazard = (result?.hazard_type || scenario.hazard_type || 'flood') as HazardType
  const totalPop = scenario.zones.reduce((s, z) => s + z.affected_population, 0)
  const avgRisk = result ? averageBaselineRisk(result) : null
  const avgRt = result ? averageBaselineResponseTime(result) : null
  const bottleneck = result ? primaryBottleneck(result) : null

  const items = [
    { label: 'Active hazard', value: HAZARD_LABELS[hazard] },
    { label: 'Population at risk', value: totalPop.toLocaleString() },
    {
      label: 'Avg risk',
      value: isRunning ? '…' : avgRisk != null ? avgRisk.toFixed(1) : '—',
    },
    {
      label: 'Avg response',
      value: isRunning ? '…' : avgRt != null ? `${avgRt.toFixed(1)} min` : '—',
    },
    {
      label: 'Primary bottleneck',
      value: bottleneck?.description ?? (result ? 'None flagged' : 'Run simulation'),
      compact: true,
    },
  ]

  return (
    <aside className="ops-summary-rail" aria-label="Situation summary">
      <p className="section-kicker">SITUATION</p>
      <h2 className="ops-summary-rail-title">Summary</h2>
      <ul className="ops-summary-rail-list">
        {items.map(item => (
          <li key={item.label} className="ops-summary-rail-item">
            <span className="ops-metric-label">{item.label}</span>
            <span
              className={item.compact ? 'ops-summary-rail-value-compact' : 'ops-metric-value'}
              style={item.compact ? undefined : { fontSize: item.label.includes('Population') ? '22px' : '26px' }}
            >
              {item.value}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  )
}
