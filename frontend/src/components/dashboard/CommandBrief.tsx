import type { HazardType, Scenario, SimulationResult } from '../../types'
import {
  averageBaselineResponseTime,
  averageBaselineRisk,
  findRecommendedIntervention,
  highestRiskZone,
  primaryBottleneck,
  riskLevelHeadline,
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

export function CommandBrief({ scenario, result, isRunning }: Props) {
  if (!result || isRunning) {
    return (
      <section
        className="command-brief command-brief-hero command-brief-empty"
        aria-label="Response command brief"
      >
        <div className="command-brief-hero-top">
          <p className="command-brief-hero-title">🚨 RESPONSE COMMAND BRIEF</p>
          <span className="ops-mode-pill"><i /> Simulation mode</span>
        </div>
        <h2 className="command-brief-title">{scenario.name}</h2>
        <p className="muted">
          Run a deterministic simulation to populate the command brief with risk, bottleneck, and
          intervention guidance. Prototype assumptions only — not real-time emergency data.
        </p>
      </section>
    )
  }

  const hazard = (result.hazard_type || scenario.hazard_type || 'flood') as HazardType
  const hazardLabel = HAZARD_LABELS[hazard]
  const locationLine = scenario.location_name || scenario.name
  const avgRisk = averageBaselineRisk(result)
  const avgRt = averageBaselineResponseTime(result)
  const topZone = highestRiskZone(result, scenario)
  const bottleneck = primaryBottleneck(result)
  const recommended = findRecommendedIntervention(result)

  return (
    <section className="command-brief command-brief-hero" aria-label="Response command brief">
      <div className="command-brief-hero-top">
        <div>
          <p className="command-brief-hero-title">🚨 RESPONSE COMMAND BRIEF</p>
          <h2 className="command-brief-title">
            {hazardLabel} · {locationLine.split(',')[0]?.trim() || locationLine}
          </h2>
          <p className="muted command-brief-subtitle">
            {scenario.source_incident_id
              ? `Simulation from incident ${scenario.source_incident_id} · deterministic prototype`
              : 'Deterministic simulation · prototype decision support'}
          </p>
        </div>
        <span className="ops-mode-pill"><i /> Simulation mode</span>
      </div>

      <div className="command-brief-metric-row command-brief-metric-row-hero">
        <div className={`ops-metric-tile risk-${topZone?.riskLevel ?? 'low'}`}>
          <p className="ops-metric-value">{avgRisk?.toFixed(1) ?? '—'}</p>
          <p className="ops-metric-label">Avg risk</p>
        </div>
        <div className="ops-metric-tile">
          <p className="ops-metric-value">{avgRt != null ? `${avgRt.toFixed(1)} min` : '—'}</p>
          <p className="ops-metric-label">Response time</p>
        </div>
        <div className="ops-metric-tile">
          <p className="ops-metric-value">{topZone?.zoneName ?? '—'}</p>
          <p className="ops-metric-label">Highest-risk zone</p>
        </div>
      </div>

      {bottleneck && (
        <div className="command-brief-block command-brief-bottleneck">
          <p className="command-brief-label">⚠ Primary bottleneck</p>
          <p className="command-brief-value">{bottleneck.description}</p>
        </div>
      )}

      {recommended && (
        <div className="command-brief-block">
          <p className="command-brief-label">Recommended response</p>
          <p className="command-brief-recommendation">{recommended.label}</p>
          {topZone && (
            <span className={`command-brief-risk-pill risk-${topZone.riskLevel}`}>
              {riskLevelHeadline(topZone.riskLevel)}
            </span>
          )}
        </div>
      )}
    </section>
  )
}
