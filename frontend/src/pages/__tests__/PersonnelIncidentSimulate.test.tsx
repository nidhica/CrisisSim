import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import { PersonnelIncidentDetailPage } from '../PersonnelIncidentDetailPage'
import * as incidents from '../../services/incidents'
import * as scenarios from '../../services/scenarios'
import * as createFromIncident from '../../services/createScenarioFromIncident'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const baseIncident = {
  incident_id: 'INC-2026-0001',
  hazard_type: 'fire' as const,
  location_name: 'Bhopal, India',
  latitude: 23.25,
  longitude: 77.41,
  severity: 'high' as const,
  description: 'Heavy smoke',
  status: 'reported' as const,
  created_at: '2026-01-01T00:00:00.000Z',
}

function renderPage() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/personnel/incidents/INC-2026-0001']}>
        <Routes>
          <Route path="/personnel/incidents/:incidentId" element={<PersonnelIncidentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('PersonnelIncidentDetailPage Simulate Response', () => {
  beforeEach(() => {
    mockNavigate.mockReset()
    vi.spyOn(incidents, 'getIncident').mockImplementation(async () => baseIncident)
    vi.spyOn(scenarios, 'getScenarios').mockResolvedValue([
      { scenario_id: 'fire-scenario-001', name: 'Fire', description: '', severity: 'high', hazard_type: 'fire' },
    ])
    vi.spyOn(createFromIncident, 'createDemoScenarioFromIncident').mockResolvedValue({
      id: 'demo-1',
      sourceScenarioId: 'fire-scenario-001',
      scenario: {
        scenario_id: 'fire-scenario-001',
        name: 'Bhopal Fire',
        description: '',
        severity: 'high',
        created_at: '',
        hazard_type: 'fire',
        population_max: 1000,
        zones: [],
        shelters: [],
        hospitals: [],
        source_incident_id: 'INC-2026-0001',
        latitude: 23.25,
        longitude: 77.41,
      },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not show simulate button for reported incidents', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/acknowledge.*before/i)).toBeInTheDocument()
    })
    expect(screen.queryByRole('button', { name: /simulate response/i })).not.toBeInTheDocument()
  })

  it('shows simulate button for acknowledged incidents', async () => {
    vi.spyOn(incidents, 'getIncident').mockResolvedValue({
      ...baseIncident,
      status: 'acknowledged',
    })
    renderPage()
    expect(await screen.findByRole('button', { name: /simulate response/i })).toBeInTheDocument()
  })

  it('navigates to simulation route after simulate', async () => {
    const user = userEvent.setup()
    vi.spyOn(incidents, 'getIncident').mockResolvedValue({
      ...baseIncident,
      status: 'assessing',
    })
    renderPage()
    await user.click(await screen.findByRole('button', { name: /simulate response/i }))
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/scenario/fire-scenario-001?demo=demo-1')
    })
  })

  it('shows error when hazard template is missing', async () => {
    const user = userEvent.setup()
    vi.spyOn(incidents, 'getIncident').mockResolvedValue({
      ...baseIncident,
      status: 'acknowledged',
    })
    vi.spyOn(createFromIncident, 'createDemoScenarioFromIncident').mockRejectedValue(
      new createFromIncident.ScenarioFromIncidentError(
        'Unable to create a simulation template for this hazard.',
      ),
    )
    renderPage()
    await user.click(await screen.findByRole('button', { name: /simulate response/i }))
    expect(
      await screen.findByText(/unable to create a simulation template/i),
    ).toBeInTheDocument()
  })
})
