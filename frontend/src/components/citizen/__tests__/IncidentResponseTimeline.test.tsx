import { render, screen } from '@testing-library/react'
import { IncidentResponseTimeline } from '../IncidentResponseTimeline'
import type { Incident } from '../../../types'

const incident: Incident = {
  incident_id: 'INC-2026-0001',
  hazard_type: 'fire',
  location_name: 'Bhopal',
  latitude: 23.25,
  longitude: 77.41,
  severity: 'high',
  description: 'Smoke',
  status: 'acknowledged',
  created_at: '2026-01-01T00:00:00.000Z',
}

describe('IncidentResponseTimeline', () => {
  it('highlights current status', () => {
    render(
      <IncidentResponseTimeline incident={incident} simulationLinked={false} />,
    )
    expect(screen.getByText(/response timeline/i)).toBeInTheDocument()
    expect(screen.getByText('Acknowledged')).toBeInTheDocument()
  })

  it('shows simulation created when linked', () => {
    render(
      <IncidentResponseTimeline incident={incident} simulationLinked simulationCreatedThisSession />,
    )
    expect(screen.getByText(/simulation created/i)).toBeInTheDocument()
    expect(screen.getByText(/INC-2026-0001/)).toBeInTheDocument()
  })
})
