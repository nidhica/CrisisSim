import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import { CitizenDashboardPage } from '../CitizenDashboardPage'
import * as incidents from '../../services/incidents'

vi.mock('../../services/scenarios', () => ({
  getScenarios: vi.fn().mockResolvedValue([
    { scenario_id: 'demo-flood', name: 'Demo', description: '', severity: 'high', hazard_type: 'flood' },
  ]),
  getScenario: vi.fn().mockResolvedValue({
    scenario_id: 'demo-flood',
    name: 'Demo Flood',
    description: 'Demo',
    severity: 'high',
    created_at: '2026-01-01',
    hazard_type: 'flood',
    population_max: 1000,
    zones: [],
    shelters: [
      { shelter_id: 's1', name: 'Shelter', coordinates: [0, 0], capacity: 100, current_occupancy: 10 },
    ],
    hospitals: [
      {
        hospital_id: 'h1',
        name: 'Hospital',
        coordinates: [0, 0],
        capacity: 50,
        surge_capacity: 10,
        current_occupancy: 5,
      },
    ],
  }),
}))

describe('CitizenDashboardPage My Reports', () => {
  beforeEach(() => {
    vi.spyOn(incidents, 'getIncidents').mockResolvedValue([
      {
        incident_id: 'INC-2026-0001',
        hazard_type: 'fire',
        location_name: 'Bhopal, Madhya Pradesh, India',
        latitude: 23.25,
        longitude: 77.41,
        severity: 'high',
        description: 'Smoke',
        status: 'reported',
        created_at: '2026-01-01T00:00:00.000Z',
      },
    ])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists submitted reports from the API', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <CitizenDashboardPage />
        </MemoryRouter>
      </AuthProvider>,
    )
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /demo flood/i })).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: /report a crisis/i })).toBeInTheDocument()
    expect(screen.getByText('INC-2026-0001')).toBeInTheDocument()
    expect(screen.getByText(/bhopal/i)).toBeInTheDocument()
    expect(screen.getByText(/reported/i)).toBeInTheDocument()
    expect(incidents.getIncidents).toHaveBeenCalled()
  })
})
