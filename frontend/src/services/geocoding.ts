import type { GeoLocation } from '../types'

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
const MAX_RESULTS = 5

export type GeocodingErrorCode = 'NO_RESULTS' | 'NETWORK' | 'RATE_LIMIT' | 'MALFORMED' | 'EMPTY_QUERY'

export class GeocodingError extends Error {
  readonly code: GeocodingErrorCode

  constructor(message: string, code: GeocodingErrorCode) {
    super(message)
    this.name = 'GeocodingError'
    this.code = code
  }
}

interface NominatimResult {
  display_name?: string
  lat?: string
  lon?: string
}

/**
 * Search OpenStreetMap Nominatim for a location.
 * Call only on explicit user submit — not on every keystroke.
 */
export async function searchLocation(query: string): Promise<GeoLocation[]> {
  const trimmed = query.trim()
  if (!trimmed) {
    throw new GeocodingError('Enter a location to search.', 'EMPTY_QUERY')
  }

  const params = new URLSearchParams({
    q: trimmed,
    format: 'json',
    limit: String(MAX_RESULTS),
    addressdetails: '0',
  })

  let response: Response
  try {
    response = await fetch(`${NOMINATIM_URL}?${params.toString()}`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Accept-Language': 'en',
      },
    })
  } catch {
    throw new GeocodingError(
      'Location search is unavailable. Please try again.',
      'NETWORK',
    )
  }

  if (response.status === 429) {
    throw new GeocodingError(
      'Location search is temporarily rate-limited. Please wait a moment and try again.',
      'RATE_LIMIT',
    )
  }

  if (!response.ok) {
    throw new GeocodingError(
      'Location search is unavailable. Please try again.',
      'NETWORK',
    )
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new GeocodingError(
      'Location search returned an invalid response. Please try again.',
      'MALFORMED',
    )
  }

  if (!Array.isArray(payload)) {
    throw new GeocodingError(
      'Location search returned an invalid response. Please try again.',
      'MALFORMED',
    )
  }

  const results: GeoLocation[] = []
  for (const item of payload as NominatimResult[]) {
    if (!item || typeof item !== 'object') continue
    const lat = Number.parseFloat(item.lat ?? '')
    const lon = Number.parseFloat(item.lon ?? '')
    const displayName = item.display_name?.trim()
    if (!displayName || !Number.isFinite(lat) || !Number.isFinite(lon)) continue
    results.push({ displayName, latitude: lat, longitude: lon })
  }

  if (results.length === 0) {
    throw new GeocodingError('No matching location found.', 'NO_RESULTS')
  }

  return results
}
