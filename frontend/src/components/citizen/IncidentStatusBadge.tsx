import type { IncidentStatus } from '../../types'
import { formatIncidentStatus } from '../../constants/hazardDisplay'

interface Props {
  status: IncidentStatus
}

export function IncidentStatusBadge({ status }: Props) {
  return (
    <span className={`incident-status incident-status-${status}`}>
      ● {formatIncidentStatus(status)}
    </span>
  )
}
