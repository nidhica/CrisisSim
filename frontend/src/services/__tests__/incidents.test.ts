import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import api from '../api'
import { createIncident, getIncident, getIncidents, updateIncident } from '../incidents'

vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('incidents API service', () => {
  beforeEach(() => {
    vi.mocked(api.post).mockReset()
    vi.mocked(api.get).mockReset()
    vi.mocked(api.patch).mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('createIncident posts to the API', async () => {
    const incident = {
      incident_id: 'INC-2026-0001',
      hazard_type: 'fire' as const,
      location_name: 'Bhopal',
      latitude: 23.25,
      longitude: 77.41,
      severity: 'high' as const,
      description: 'Smoke',
      status: 'reported' as const,
      created_at: '2026-01-01T00:00:00.000Z',
    }
    vi.mocked(api.post).mockResolvedValue({ data: incident })
    const result = await createIncident({
      hazard_type: 'fire',
      location_name: 'Bhopal',
      latitude: 23.25,
      longitude: 77.41,
      severity: 'high',
      description: 'Smoke',
    })
    expect(api.post).toHaveBeenCalledWith('/incidents', {
      hazard_type: 'fire',
      location_name: 'Bhopal',
      latitude: 23.25,
      longitude: 77.41,
      severity: 'high',
      description: 'Smoke',
    })
    expect(result.incident_id).toBe('INC-2026-0001')
  })

  it('getIncidents returns incidents from the API', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { incidents: [{ incident_id: 'INC-2026-0001' }] } })
    const list = await getIncidents()
    expect(api.get).toHaveBeenCalledWith('/incidents')
    expect(list).toHaveLength(1)
  })

  it('updateIncident patches status', async () => {
    vi.mocked(api.patch).mockResolvedValue({
      data: { incident_id: 'INC-2026-0001', status: 'acknowledged' },
    })
    const updated = await updateIncident('INC-2026-0001', 'acknowledged')
    expect(api.patch).toHaveBeenCalledWith('/incidents/INC-2026-0001', { status: 'acknowledged' })
    expect(updated.status).toBe('acknowledged')
  })

  it('getIncident returns null on 404', async () => {
    vi.mocked(api.get).mockRejectedValue(
      new axios.AxiosError('Not found', 'ERR', undefined, undefined, {
        status: 404,
        data: {},
        statusText: 'Not Found',
        headers: {},
        config: {} as import('axios').InternalAxiosRequestConfig,
      }),
    )
    const result = await getIncident('missing')
    expect(result).toBeNull()
  })
})
