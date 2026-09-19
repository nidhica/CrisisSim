import { useState } from 'react'
import type { GeoLocation } from '../../types'
import { GeocodingError, searchLocation } from '../../services/geocoding'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  selectedLocation: GeoLocation | null
  onLocationChange: (location: GeoLocation | null) => void
  helperText: string
  fieldError?: string | null
}

export function LocationSearchPicker({
  selectedLocation,
  onLocationChange,
  helperText,
  fieldError,
}: Props) {
  const [locationQuery, setLocationQuery] = useState('')
  const [locationResults, setLocationResults] = useState<GeoLocation[]>([])
  const [locationSearching, setLocationSearching] = useState(false)
  const [locationMessage, setLocationMessage] = useState<string | null>(null)

  async function handleLocationSearch() {
    setLocationSearching(true)
    setLocationMessage(null)
    setLocationResults([])
    onLocationChange(null)
    try {
      const results = await searchLocation(locationQuery)
      setLocationResults(results)
      setLocationMessage(
        results.length === 1
          ? 'One location found. Select it to continue.'
          : `${results.length} locations found. Select the correct match.`,
      )
    } catch (e: unknown) {
      if (e instanceof GeocodingError) {
        setLocationMessage(e.message)
      } else {
        setLocationMessage('Location search is unavailable. Please try again.')
      }
    } finally {
      setLocationSearching(false)
    }
  }

  function selectLocation(location: GeoLocation) {
    onLocationChange(location)
    setLocationMessage(null)
  }

  return (
    <div className="location-picker">
      <p className="muted location-helper">{helperText}</p>
      <div className="form-grid two">
        <label>
          Search location
          <input
            value={locationQuery}
            onChange={e => setLocationQuery(e.target.value)}
            placeholder="e.g. Bhopal, Madhya Pradesh"
            aria-invalid={fieldError ? true : undefined}
          />
        </label>
        <div className="location-search-actions">
          <button
            type="button"
            className="button button-secondary location-search-button"
            disabled={locationSearching || !locationQuery.trim()}
            onClick={handleLocationSearch}
          >
            {locationSearching ? 'Searching…' : 'Search location'}
          </button>
        </div>
      </div>
      {fieldError && <p className="field-error" role="alert">{fieldError}</p>}
      {locationSearching && (
        <div className="mt-2">
          <LoadingSpinner label="Searching locations..." />
        </div>
      )}
      {locationMessage && (
        <p className={`location-message ${locationResults.length ? 'info' : 'warn'}`}>
          {locationMessage}
        </p>
      )}
      {locationResults.length > 0 && (
        <div className="location-results">
          <p className="eyebrow">Location results</p>
          <ul>
            {locationResults.map(result => (
              <li key={`${result.latitude}-${result.longitude}-${result.displayName}`}>
                <button
                  type="button"
                  className={
                    selectedLocation?.displayName === result.displayName &&
                    selectedLocation.latitude === result.latitude
                      ? 'location-result selected'
                      : 'location-result'
                  }
                  onClick={() => selectLocation(result)}
                >
                  {result.displayName}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {selectedLocation && (
        <div className="selected-location">
          <p className="eyebrow">Selected location</p>
          <p>
            <strong>{selectedLocation.displayName}</strong>
          </p>
          <p className="muted">
            Coordinates: {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
          </p>
        </div>
      )}
    </div>
  )
}
