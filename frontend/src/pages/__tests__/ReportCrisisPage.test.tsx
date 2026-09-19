import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import { ReportCrisisPage } from '../ReportCrisisPage'
import * as incidents from '../../services/incidents'
import * as geocoding from '../../services/geocoding'

function renderReportPage() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <ReportCrisisPage />
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('ReportCrisisPage', () => {
  beforeEach(() => {
    vi.spyOn(geocoding, 'searchLocation').mockResolvedValue([
      {
        displayName: 'Bhopal, Madhya Pradesh, India',
        latitude: 23.2599,
        longitude: 77.4126,
      },
    ])
    vi.spyOn(incidents, 'createIncident').mockResolvedValue({
      incident_id: 'INC-2026-0001',
      hazard_type: 'fire',
      location_name: 'Bhopal, Madhya Pradesh, India',
      latitude: 23.2599,
      longitude: 77.4126,
      severity: 'high',
      description: 'Heavy smoke near the market.',
      status: 'reported',
      created_at: '2026-01-01T00:00:00.000Z',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the report form', () => {
    renderReportPage()
    expect(screen.getByRole('heading', { name: /report a crisis/i })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /incident type/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit report/i })).toBeInTheDocument()
  })

  it('allows selecting all five hazards', async () => {
    const user = userEvent.setup()
    renderReportPage()
    const group = screen.getByRole('group', { name: /incident type/i })
    const labels = ['Fire', 'Flood', 'Earthquake', 'Cyclone', 'Industrial']
    for (const label of labels) {
      const button = within(group).getByRole('button', { name: new RegExp(`^${label}`, 'i') })
      await user.click(button)
      expect(button).toHaveAttribute('aria-pressed', 'true')
    }
  })

  it('requires explicit location selection from search results', async () => {
    const user = userEvent.setup()
    renderReportPage()
    await user.type(screen.getByPlaceholderText(/bhopal/i), 'Bhopal')
    await user.click(screen.getByRole('button', { name: /search location/i }))
    expect(await screen.findByText(/bhopal, madhya pradesh/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /bhopal, madhya pradesh/i }))
    expect(screen.getByText(/selected location/i)).toBeInTheDocument()
  })

  it('shows validation errors when required fields are missing', async () => {
    const user = userEvent.setup()
    renderReportPage()
    await user.click(screen.getByRole('button', { name: /submit report/i }))
    expect(screen.getByText(/select the type of incident/i)).toBeInTheDocument()
    expect(screen.getByText(/search for a location/i)).toBeInTheDocument()
    expect(screen.getByText(/select how severe/i)).toBeInTheDocument()
    expect(screen.getByText(/describe what you are seeing/i)).toBeInTheDocument()
  })

  it('submits a valid report through the API', async () => {
    const user = userEvent.setup()
    renderReportPage()

    await user.click(
      within(screen.getByRole('group', { name: /incident type/i })).getByRole('button', {
        name: /^Fire/i,
      }),
    )
    await user.type(screen.getByPlaceholderText(/bhopal/i), 'Bhopal')
    await user.click(screen.getByRole('button', { name: /search location/i }))
    await user.click(await screen.findByRole('button', { name: /bhopal, madhya pradesh/i }))
    await user.click(within(screen.getByRole('group', { name: /severity/i })).getByRole('button', { name: 'High' }))
    await user.type(
      screen.getByPlaceholderText(/describe what you are seeing/i),
      'Heavy smoke near the market.',
    )
    await user.click(screen.getByRole('button', { name: /submit report/i }))

    expect(await screen.findByRole('heading', { name: /report submitted/i })).toBeInTheDocument()
    expect(screen.getByText('INC-2026-0001')).toBeInTheDocument()
    expect(incidents.createIncident).toHaveBeenCalledTimes(1)
  })
})
