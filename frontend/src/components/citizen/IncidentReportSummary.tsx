import type { Incident } from '../../types'
import { formatIncidentStatus, hazardEmoji, hazardLabel } from '../../constants/hazardDisplay'
import { IncidentStatusBadge } from './IncidentStatusBadge'

interface Props {
  incident: Incident
  title?: string
}

export function IncidentReportSummary({ incident, title = 'Report Submitted' }: Props) {
  return (
    <section className="report-confirmation content-card" aria-labelledby="report-confirmation-title">
      <h2 id="report-confirmation-title">{title}</h2>
      <hr className="report-divider" />
      <dl className="report-details">
        <div>
          <dt>Incident ID</dt>
          <dd>{incident.incident_id}</dd>
        </div>
        <div>
          <dt>Hazard</dt>
          <dd>{hazardEmoji(incident.hazard_type)} {hazardLabel(incident.hazard_type)}</dd>
        </div>
        <div>
          <dt>Location</dt>
          <dd>{incident.location_name}</dd>
        </div>
        <div>
          <dt>Severity</dt>
          <dd className="capitalize">{incident.severity}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>
            <IncidentStatusBadge status={incident.status} />
          </dd>
        </div>
      </dl>
      <p className="muted report-notice">
        Your report has been recorded in the CrisisSim prototype. It has been recorded for authority
        review.
      </p>
      <p className="muted report-disclaimer">
        This prototype does not provide real emergency response services. CrisisSim does not use
        citizen reports as real-time emergency data.
      </p>
    </section>
  )
}

export function incidentListLocationShort(name: string): string {
  const first = name.split(',')[0]?.trim()
  return first || name
}

export function incidentStatusLabel(status: Incident['status']): string {
  return formatIncidentStatus(status)
}
