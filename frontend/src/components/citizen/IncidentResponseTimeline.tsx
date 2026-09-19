import type { Incident, IncidentStatus } from '../../types'

const STEPS: { key: string; label: string; shortLabel: string; status?: IncidentStatus }[] = [
  { key: 'report', label: 'Reported', shortLabel: 'Report', status: 'reported' },
  { key: 'ack', label: 'Acknowledged', shortLabel: 'Acknowledge', status: 'acknowledged' },
  { key: 'assess', label: 'Assessing', shortLabel: 'Assess', status: 'assessing' },
  { key: 'sim', label: 'Simulation', shortLabel: 'Simulate' },
  { key: 'dispatch', label: 'Response dispatched', shortLabel: 'Response', status: 'response_dispatched' },
  { key: 'resolved', label: 'Resolved', shortLabel: 'Resolved', status: 'resolved' },
]

const STATUS_ORDER: IncidentStatus[] = [
  'reported',
  'acknowledged',
  'assessing',
  'response_dispatched',
  'resolved',
]

function statusIndex(status: IncidentStatus): number {
  return STATUS_ORDER.indexOf(status)
}

interface Props {
  incident: Incident
  simulationLinked: boolean
  simulationCreatedThisSession?: boolean
  layout?: 'default' | 'vertical'
}

export function IncidentResponseTimeline({
  incident,
  simulationLinked,
  simulationCreatedThisSession,
  layout = 'default',
}: Props) {
  const currentIdx = statusIndex(incident.status)
  const isVertical = layout === 'vertical'

  return (
    <section
      className={`incident-timeline${isVertical ? ' incident-timeline-vertical' : ''}`}
      aria-label="Incident response timeline"
    >
      {!isVertical && (
        <>
          <p className="section-kicker">RESPONSE TIMELINE</p>
          <p className="muted">
            Citizen report → authority assessment → simulation (optional) → response workflow.
          </p>
        </>
      )}
      <ol className="incident-timeline-list">
        {STEPS.flatMap((step, index) => {
          const isSimStep = step.key === 'sim'
          const stepStatusIdx = step.status != null ? statusIndex(step.status) : -1
          const isCurrent = step.status != null && incident.status === step.status
          const isComplete =
            step.status != null
              ? currentIdx > stepStatusIdx
              : isSimStep && (simulationLinked || simulationCreatedThisSession)
          const state = isCurrent ? 'current' : isComplete ? 'complete' : 'upcoming'

          const nodes = []
          if (isVertical && index > 0) {
            nodes.push(
              <li key={`${step.key}-connector`} className="incident-timeline-connector-item" aria-hidden>
                ↓
              </li>,
            )
          }
          nodes.push(
            <li key={step.key} className={`incident-timeline-step ${state}`}>
              <span className="incident-timeline-marker" aria-hidden />
              <div>
                <strong>{isVertical ? step.shortLabel.toUpperCase() : step.label}</strong>
                {!isVertical && isSimStep && (simulationLinked || simulationCreatedThisSession) && (
                  <p className="muted">
                    Simulation created
                    {simulationLinked ? ` · linked to ${incident.incident_id}` : ''}
                  </p>
                )}
                {isVertical && isCurrent && <p className="muted">Current status</p>}
                {isVertical && isSimStep && (simulationLinked || simulationCreatedThisSession) && (
                  <p className="muted">Simulation linked</p>
                )}
              </div>
            </li>,
          )
          return nodes
        })}
      </ol>
    </section>
  )
}
