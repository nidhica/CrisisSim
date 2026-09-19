import type { Bottleneck } from '../../types'

interface Props {
  bottlenecks: Bottleneck[]
  hazardLabel?: string
}

const typeIcons: Record<string, string> = {
  resource_shortage: '🚒',
  shelter_capacity: '🏠',
  hospital_capacity: '🏥',
  road_access: '🛣️',
  blocked_access: '🚧',
  fire_crew_shortage: '🔥',
  uncontrolled_spread: '🔥',
  smoke_medical_pressure: '💨',
  search_and_rescue_shortage: '⛑️',
  structural_rescue_backlog: '🏚️',
  medical_pressure: '🏥',
  evacuation_capacity: '🚌',
  utility_restoration_shortage: '⚡',
  hazmat_shortage: '☣️',
  containment_shortage: '🧪',
  toxic_medical_pressure: '☣️',
  toxic_exposure: '☢️',
}

export function BottleneckAlert({ bottlenecks, hazardLabel }: Props) {
  if (bottlenecks.length === 0) {
    return (
      <div className="content-card ops-bottleneck-none" style={{ padding: '12px 14px', fontSize: '13px' }}>
        ✓ No critical bottlenecks detected in this simulation run
        {hazardLabel ? ` (${hazardLabel.toLowerCase()} scenario)` : ''}
      </div>
    )
  }

  const primary = bottlenecks[0]
  const zoneName = primary.zone_id
    ? primary.zone_id.replace(/^zone-/, 'Zone ').replace(/-/g, ' ')
    : null

  return (
    <div className="ops-bottleneck-card" role="alert">
      <p className="command-brief-label" style={{ margin: 0 }}>
        ⚠ Primary bottleneck
        {hazardLabel && (
          <span className="muted" style={{ marginLeft: 8, fontWeight: 600 }}>
            · {hazardLabel}
          </span>
        )}
      </p>
      {zoneName && (
        <p style={{ margin: '8px 0 0', fontWeight: 700, color: '#f8fafc' }}>{zoneName}</p>
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 8, fontSize: '14px' }}>
        <span aria-hidden>{typeIcons[primary.type] || '⚠️'}</span>
        <div>
          <strong style={{ color: '#fde68a' }}>{primary.description}</strong>
          <p className="muted" style={{ margin: '8px 0 0', fontSize: '12px' }}>
            Specialist resources and capacity limits are modeled as the limiting factor under the
            current simulation assumptions.
          </p>
        </div>
      </div>
      {bottlenecks.length > 1 && (
        <p className="muted" style={{ margin: '10px 0 0', fontSize: '11px' }}>
          +{bottlenecks.length - 1} additional bottleneck{bottlenecks.length > 2 ? 's' : ''} in
          simulation output (severity {primary.severity_score.toFixed(2)})
        </p>
      )}
    </div>
  )
}
