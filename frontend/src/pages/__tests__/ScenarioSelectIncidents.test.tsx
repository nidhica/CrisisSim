import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import { ScenarioSelectPage } from '../ScenarioSelectPage'
import * as incidents from '../../services/incidents'

vi.mock('../../services/scenarios', () => ({
  getScenarios: vi.fn().mockResolvedValue([]),
}))

describe('ScenarioSelectPage incident command center', () => {
  beforeEach(() => {
    vi.spyOn(incidents, 'getIncidents').mockResolvedValue([
      {
        incident_id: 'INC-2026-0001',
        hazard_type: 'fire',
        location_name: 'Bhopal, India',
        latitude: 23.25,
        longitude: 77.41,
        severity: 'critical',
        description: 'Smoke',
        status: 'reported',
        created_at: '2026-01-01T00:00:00.000Z',
      },
      {
        incident_id: 'INC-2026-0002',
        hazard_type: 'flood',
        location_name: 'Chennai, India',
        latitude: 13.08,
        longitude: 80.27,
        severity: 'high',
        description: 'Water',
        status: 'resolved',
        created_at: '2026-01-02T00:00:00.000Z',
      },
    ])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows summary counts and incoming incidents', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <ScenarioSelectPage />
        </MemoryRouter>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /incident command center/i })).toBeInTheDocument()
    })

    const summaryCards = screen.getAllByText('1')
    expect(summaryCards.length).toBeGreaterThanOrEqual(3)
    expect(screen.getByText('INC-2026-0001')).toBeInTheDocument()
    const firstCard = screen.getByText('INC-2026-0001').closest('.incident-incoming-card')
    expect(firstCard?.querySelector('a.incident-view-link')).toHaveAttribute(
      'href',
      '/personnel/incidents/INC-2026-0001',
    )
  })
})
