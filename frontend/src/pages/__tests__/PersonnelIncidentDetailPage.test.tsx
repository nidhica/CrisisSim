import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import { PersonnelIncidentDetailPage } from '../PersonnelIncidentDetailPage'
import * as incidents from '../../services/incidents'

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

describe('PersonnelIncidentDetailPage', () => {
  beforeEach(() => {
    vi.spyOn(incidents, 'getIncident').mockResolvedValue(baseIncident)
    vi.spyOn(incidents, 'updateIncident').mockResolvedValue({
      ...baseIncident,
      status: 'acknowledged',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads and displays the incident', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /INC-2026-0001/ })).toBeInTheDocument()
    })
    expect(screen.getByText(/heavy smoke/i)).toBeInTheDocument()
  })

  it('sends PATCH when acknowledging', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge incident/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /acknowledge incident/i }))
    await waitFor(() => {
      expect(incidents.updateIncident).toHaveBeenCalledWith('INC-2026-0001', 'acknowledged')
    })
    expect(await screen.findByText('● acknowledged')).toBeInTheDocument()
  })
})
