import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { GeoLocation, HazardType, ScenarioSummary } from '../types'
import { getScenario, getScenarios } from '../services/scenarios'
import { createDemoScenario } from '../services/demoScenarios'
import { GeocodingError, searchLocation } from '../services/geocoding'
import { locationShortName } from '../services/generateLocationScenarioGeometry'
import { Header } from '../components/layout/Header'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useNavigate } from 'react-router-dom'
import {
  DEFAULT_HAZARD_FACTORS,
  HAZARD_FACTOR_KEYS,
  HAZARD_SCENARIO_META,
} from '../constants/hazardScenarioDefaults'

const HAZARDS = HAZARD_SCENARIO_META
const factorKeys = HAZARD_FACTOR_KEYS
const DEFAULT_FACTORS = DEFAULT_HAZARD_FACTORS

export function CreateEmergencyScenarioPage() {
  const navigate = useNavigate()
  const [sources, setSources] = useState<ScenarioSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hazard, setHazard] = useState<HazardType>('flood')
  const [name, setName] = useState('')
  const [severity, setSeverity] = useState('high')
  const [affectedZones, setAffectedZones] = useState(2)
  const [population, setPopulation] = useState(1200)
  const [medical, setMedical] = useState(0.6)
  const [road, setRoad] = useState(0.45)
  const [factors, setFactors] = useState(DEFAULT_FACTORS.flood)
  const [resources, setResources] = useState<Record<string, number>>({})
  const [rescueTeams, setRescueTeams] = useState(4)
  const [ambulances, setAmbulances] = useState(2)
  const [locationQuery, setLocationQuery] = useState('')
  const [locationResults, setLocationResults] = useState<GeoLocation[]>([])
  const [selectedLocation, setSelectedLocation] = useState<GeoLocation | null>(null)
  const [locationSearching, setLocationSearching] = useState(false)
  const [locationMessage, setLocationMessage] = useState<string | null>(null)

  useEffect(() => {
    getScenarios()
      .then(setSources)
      .catch((e: unknown) => setError((e as Error).message || 'Failed to load scenario bases'))
      .finally(() => setLoading(false))
  }, [])

  function chooseHazard(value: HazardType) {
    setHazard(value)
    setFactors(DEFAULT_FACTORS[value])
    setResources(Object.fromEntries(HAZARDS[value].resources.map(key => [key, 2])))
    setError(null)
  }

  async function handleLocationSearch() {
    setLocationSearching(true)
    setLocationMessage(null)
    setLocationResults([])
    setSelectedLocation(null)
    setError(null)
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
    setSelectedLocation(location)
    setLocationMessage(null)
    if (!name.trim()) {
      setName(`${locationShortName(location.displayName)} ${HAZARDS[hazard].label} Emergency`)
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    const sourceSummary = sources.find(source => source.hazard_type === hazard)
    if (!sourceSummary) {
      setError(`No demo base scenario is available for ${HAZARDS[hazard].label}. Check that the API is running.`)
      return
    }
    if (locationResults.length > 0 && !selectedLocation) {
      setError('Select a location from the search results before creating the scenario.')
      return
    }

    const scenarioName =
      name.trim() ||
      (selectedLocation
        ? `${locationShortName(selectedLocation.displayName)} ${HAZARDS[hazard].label} Emergency`
        : '')

    if (!scenarioName) {
      setError('Enter a scenario name or search and select a location.')
      return
    }

    setSaving(true)
    setError(null)
    try {
      const source = await getScenario(sourceSummary.scenario_id)
      const factorMap = Object.fromEntries(
        factorKeys[hazard].map((key, index) => [key, factors[index] ?? 0]),
      )
      const demo = createDemoScenario(source, {
        name: scenarioName,
        severity: severity as 'low' | 'medium' | 'high' | 'critical',
        affectedZones,
        populationAffected: population,
        floodSeverity: factors[0],
        medicalUrgency: medical,
        roadAccessibility: road,
        rescueTeams,
        ambulances,
        hazardType: hazard,
        hazardFactors: factorMap,
        specialistResources: resources,
        location: selectedLocation ?? undefined,
        hazardLabel: HAZARDS[hazard].label,
      })
      navigate(`/scenario/${demo.sourceScenarioId}?demo=${demo.id}`)
    } catch (e: unknown) {
      setError((e as Error).message || 'Could not create the scenario configuration.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="app-shell">
        <Header />
        <main className="page-center">
          <LoadingSpinner label="Preparing scenario configuration..." />
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Header />
      <main className="create-page">
        <div className="create-heading">
          <div>
            <p className="eyebrow">OPERATIONS CENTER / NEW EMERGENCY</p>
            <h1>Register emergency scenario</h1>
            <p>
              Configure a location-aware simulated emergency scenario. Real place, simulated
              emergency — not real-time disaster data.
            </p>
          </div>
          <button className="text-button" type="button" onClick={() => navigate('/personnel')}>
            Cancel
          </button>
        </div>
        {error && <ErrorBanner message={error} />}
        <form className="scenario-form" onSubmit={submit}>
          <section className="form-section">
            <div className="form-section-heading">
              <span>01</span>
              <div>
                <h2>Incident profile</h2>
                <p>Select the hazard and scenario category.</p>
              </div>
            </div>
            <div className="form-grid two">
              <label>
                Scenario name
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder={
                    selectedLocation
                      ? `${locationShortName(selectedLocation.displayName)} ${HAZARDS[hazard].label} Emergency`
                      : `${HAZARDS[hazard].label} simulation`
                  }
                />
                <small>Leave blank to auto-generate from location and hazard.</small>
              </label>
              <label>
                Emergency type
                <select value={hazard} onChange={e => chooseHazard(e.target.value as HazardType)}>
                  {Object.entries(HAZARDS).map(([key, item]) => (
                    <option key={key} value={key}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Severity category
                <select value={severity} onChange={e => setSeverity(e.target.value)}>
                  {['low', 'medium', 'high', 'critical'].map(value => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </label>
              <label>
                Simulation base
                <output className="form-output">
                  {sources.find(source => source.hazard_type === hazard)?.name ??
                    'No compatible scenario loaded'}
                </output>
                <small>Deterministic hazard logic from the matched API scenario.</small>
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>02</span>
              <div>
                <h2>Location</h2>
                <p>
                  Search for a real-world place. Simulated zones will be generated around the
                  selected coordinates — not actual hazard boundaries.
                </p>
              </div>
            </div>
            <div className="form-grid two">
              <label>
                Location
                <input
                  value={locationQuery}
                  onChange={e => setLocationQuery(e.target.value)}
                  placeholder="e.g. Bhopal, Madhya Pradesh"
                />
              </label>
              <div className="location-search-actions">
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={locationSearching || !locationQuery.trim()}
                  onClick={handleLocationSearch}
                >
                  {locationSearching ? 'Searching…' : 'Search location'}
                </button>
              </div>
            </div>
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
                  Simulated {HAZARDS[hazard].label} emergency at{' '}
                  {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
                </p>
              </div>
            )}
            {!selectedLocation && (
              <p className="muted">
                Optional: skip location search to use the default demo geography (London template).
              </p>
            )}
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>03</span>
              <div>
                <h2>{HAZARDS[hazard].label} conditions</h2>
                <p>Hazard-specific conditions are normalized simulation inputs.</p>
              </div>
            </div>
            <div className="form-grid three">
              <Number label="Affected zones" value={affectedZones} onChange={setAffectedZones} />
              <Number label="Population per zone" value={population} onChange={setPopulation} />
              {HAZARDS[hazard].factors.map((label, index) => (
                <Range
                  key={label}
                  label={label}
                  value={factors[index] ?? 0}
                  onChange={value =>
                    setFactors(current => current.map((item, i) => (i === index ? value : item)))
                  }
                />
              ))}
              <Range label="Medical urgency" value={medical} onChange={setMedical} />
              <Range label="Road accessibility" value={road} onChange={setRoad} />
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>04</span>
              <div>
                <h2>Response resources</h2>
                <p>Values can be adjusted again in the What-If simulator.</p>
              </div>
            </div>
            <div className="form-grid two">
              {HAZARDS[hazard].resources.length ? (
                HAZARDS[hazard].resources.map(resource => (
                  <Number
                    key={resource}
                    label={resource.replaceAll('_', ' ')}
                    value={resources[resource] ?? 0}
                    onChange={value =>
                      setResources(current => ({ ...current, [resource]: value }))
                    }
                  />
                ))
              ) : (
                <>
                  <Number label="Rescue teams per zone" value={rescueTeams} onChange={setRescueTeams} />
                  <Number label="Ambulances per zone" value={ambulances} onChange={setAmbulances} />
                </>
              )}
            </div>
          </section>

          <footer className="form-footer">
            <p>
              Location-aware simulated emergency scenario. Not real-time disaster data or actual
              nearby emergency facilities.
            </p>
            <button
              className="button button-primary"
              disabled={saving || !sources.some(source => source.hazard_type === hazard)}
            >
              {saving ? 'Preparing scenario…' : 'Create and open scenario'} <span>→</span>
            </button>
          </footer>
        </form>
      </main>
    </div>
  )
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        min="0"
        value={value}
        onChange={e => onChange(globalThis.Number(e.target.value))}
      />
    </label>
  )
}
const Number = NumberField

function Range({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <label>
      {label}
      <div className="range-control">
        <input
          type="range"
          min="0"
          max="1"
          step=".05"
          value={value}
          onChange={e => onChange(globalThis.Number(e.target.value))}
        />
        <output>{Math.round(value * 100)}%</output>
      </div>
    </label>
  )
}
