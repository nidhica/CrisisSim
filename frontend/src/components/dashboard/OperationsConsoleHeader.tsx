import type { HazardType, Scenario, SimulationResult } from '../../types'

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

export function OperationsConsoleHeader({ scenario, result, isRunning }: Props) {
  const hazard = (scenario.hazard_type || 'flood') as HazardType
  const location = scenario.location_name || scenario.name

  return (
    <header className={`ops-console-header hazard-theme-${hazard}`}>
      <div>
        <p className="ops-console-header-path">CRISISSIM / OPERATIONS</p>
        <span className="ops-hazard-badge">{HAZARD_LABELS[hazard]}</span>
        <h1>{scenario.name}</h1>
        <p className="ops-console-header-location">{location}</p>
        <span className="ops-mode-pill"><i /> Simulation mode</span>
      </div>
      <div className="ops-console-header-meta">
        {scenario.source_incident_id && (
          <div>Incident <strong>{scenario.source_incident_id}</strong></div>
        )}
        <div>
          Status:{' '}
          <strong>
            {isRunning ? 'Running simulation…' : result ? 'Results available' : 'Awaiting simulation'}
          </strong>
        </div>
        {result?.run_at && (
          <div>Last simulation: {new Date(result.run_at).toLocaleString()}</div>
        )}
      </div>
    </header>
  )
}
