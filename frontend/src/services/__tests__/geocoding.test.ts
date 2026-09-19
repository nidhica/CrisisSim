import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GeocodingError, searchLocation } from '../geocoding'

describe('searchLocation', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns geocoded results on success', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        {
          display_name: 'Bhopal, Madhya Pradesh, India',
          lat: '23.2599',
          lon: '77.4126',
        },
      ],
    } as Response)

    const results = await searchLocation('Bhopal')
    expect(results).toHaveLength(1)
    expect(results[0]).toEqual({
      displayName: 'Bhopal, Madhya Pradesh, India',
      latitude: 23.2599,
      longitude: 77.4126,
    })
  })

  it('returns multiple results when available', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        { display_name: 'Bhopal, India', lat: '23.25', lon: '77.41' },
        { display_name: 'Bhopal, USA', lat: '40.1', lon: '-74.2' },
      ],
    } as Response)

    const results = await searchLocation('Bhopal')
    expect(results).toHaveLength(2)
  })

  it('throws NO_RESULTS when payload is empty', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    } as Response)

    await expect(searchLocation('Nowhereville XYZ')).rejects.toMatchObject({
      code: 'NO_RESULTS',
    })
  })

  it('throws NETWORK on fetch failure', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('offline'))

    await expect(searchLocation('Bhopal')).rejects.toMatchObject({
      code: 'NETWORK',
    })
  })

  it('throws RATE_LIMIT on HTTP 429', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => [],
    } as Response)

    await expect(searchLocation('Bhopal')).rejects.toMatchObject({
      code: 'RATE_LIMIT',
    })
  })

  it('throws MALFORMED on invalid JSON shape', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ error: 'bad' }),
    } as Response)

    await expect(searchLocation('Bhopal')).rejects.toMatchObject({
      code: 'MALFORMED',
    })
  })

  it('throws EMPTY_QUERY for blank input', async () => {
    await expect(searchLocation('   ')).rejects.toBeInstanceOf(GeocodingError)
  })
})
