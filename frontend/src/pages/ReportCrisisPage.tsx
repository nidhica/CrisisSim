import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { GeoLocation, HazardType, Incident, IncidentSeverity } from '../types'
import { CITIZEN_HAZARD_OPTIONS } from '../constants/hazardDisplay'
import { LocationSearchPicker } from '../components/location/LocationSearchPicker'
import { createIncident } from '../services/incidents'
import { Header } from '../components/layout/Header'
import { IncidentReportSummary } from '../components/citizen/IncidentReportSummary'
import { ErrorBanner } from '../components/common/ErrorBanner'

const SEVERITY_OPTIONS: { value: IncidentSeverity; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

export function ReportCrisisPage() {
  const navigate = useNavigate()
  const [hazard, setHazard] = useState<HazardType | null>(null)
  const [selectedLocation, setSelectedLocation] = useState<GeoLocation | null>(null)
  const [severity, setSeverity] = useState<IncidentSeverity | null>(null)
  const [description, setDescription] = useState('')
  const [evidencePreview, setEvidencePreview] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState<Incident | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  function validate(): Record<string, string> {
    const next: Record<string, string> = {}
    if (!hazard) next.hazard = 'Select the type of incident you are reporting.'
    if (!selectedLocation) {
      next.location = 'Search for a location and select one result before submitting.'
    }
    if (!severity) next.severity = 'Select how severe the situation appears.'
    if (!description.trim()) next.description = 'Describe what you are seeing or experiencing.'
    return next
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nextErrors = validate()
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return
    if (!hazard || !selectedLocation || !severity) return

    setSubmitting(true)
    setSubmitError(null)
    try {
      const incident = await createIncident({
        hazard_type: hazard,
        location_name: selectedLocation.displayName,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        severity,
        description: description.trim(),
      })
      setSubmitted(incident)
      setEvidencePreview(null)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setSubmitError(
        err.response?.data?.detail || err.message || 'Could not submit your report. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function handleEvidenceChange(file: File | null) {
    if (!file) {
      setEvidencePreview(null)
      return
    }
    const reader = new FileReader()
    reader.onload = () => setEvidencePreview(String(reader.result))
    reader.readAsDataURL(file)
  }

  if (submitted) {
    return (
      <div className="app-shell citizen-shell citizen-shell-premium">
        <Header mode="citizen" />
        <main className="create-page">
          <div className="create-heading">
            <div>
              <p className="eyebrow">CITIZEN REPORT</p>
              <h1>Report a Crisis</h1>
            </div>
            <Link to="/citizen" className="text-button">Back to dashboard</Link>
          </div>
          <IncidentReportSummary incident={submitted} />
          <div className="report-actions">
            <button type="button" className="button button-primary" onClick={() => navigate('/citizen')}>
              Return to Citizen Dashboard
            </button>
            <Link to={`/citizen/reports/${submitted.incident_id}`} className="button button-secondary">
              View report
            </Link>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell citizen-shell citizen-shell-premium">
      <Header mode="citizen" />
      <main className="create-page">
        <div className="create-heading">
          <div>
            <p className="eyebrow">CITIZEN REPORT</p>
            <h1>Report a Crisis</h1>
            <p>
              Submit a citizen crisis report for the CrisisSim prototype. This is not a live
              emergency hotline and does not contact real authorities.
            </p>
          </div>
          <Link to="/citizen" className="text-button">Cancel</Link>
        </div>

        <form className="scenario-form" onSubmit={handleSubmit} noValidate>
          <section className="form-section">
            <div className="form-section-heading">
              <span>01</span>
              <div>
                <h2>Incident type</h2>
                <p>What kind of hazard are you reporting?</p>
              </div>
            </div>
            <div className="hazard-card-grid" role="group" aria-label="Incident type">
              {CITIZEN_HAZARD_OPTIONS.map(option => (
                <button
                  key={option.type}
                  type="button"
                  className={
                    hazard === option.type ? 'hazard-card selected' : 'hazard-card'
                  }
                  aria-pressed={hazard === option.type}
                  aria-label={`${option.label} — ${option.subtitle}`}
                  onClick={() => {
                    setHazard(option.type)
                    setErrors(prev => {
                      const { hazard: _removed, ...rest } = prev
                      return rest
                    })
                  }}
                >
                  <span className="hazard-card-emoji" aria-hidden>{option.emoji}</span>
                  <span className="hazard-card-title">{option.label.toUpperCase()}</span>
                  <span className="hazard-card-sub">{option.subtitle}</span>
                </button>
              ))}
            </div>
            {errors.hazard && <p className="field-error" role="alert">{errors.hazard}</p>}
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>02</span>
              <div>
                <h2>Location</h2>
                <p>Where is the incident located?</p>
              </div>
            </div>
            <LocationSearchPicker
              selectedLocation={selectedLocation}
              onLocationChange={location => {
                setSelectedLocation(location)
                if (location) {
                  setErrors(prev => {
                    const { location: _removed, ...rest } = prev
                    return rest
                  })
                }
              }}
              helperText="Location identifies where the reported incident is located. CrisisSim does not use this as real-time emergency data."
              fieldError={errors.location}
            />
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>03</span>
              <div>
                <h2>Severity</h2>
                <p>How serious does the situation appear?</p>
              </div>
            </div>
            <div className="severity-choice-grid" role="group" aria-label="Severity">
              {SEVERITY_OPTIONS.map(option => (
                <button
                  key={option.value}
                  type="button"
                  className={
                    severity === option.value ? 'severity-choice selected' : 'severity-choice'
                  }
                  aria-pressed={severity === option.value}
                  onClick={() => {
                    setSeverity(option.value)
                    setErrors(prev => {
                      const { severity: _removed, ...rest } = prev
                      return rest
                    })
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {errors.severity && <p className="field-error" role="alert">{errors.severity}</p>}
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>04</span>
              <div>
                <h2>What happened?</h2>
                <p>Share what you can see — precise technical details are not required.</p>
              </div>
            </div>
            <label className="description-label">
              Description
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={5}
                placeholder="Describe what you are seeing, such as smoke, flooding, damaged buildings, blocked roads, etc."
                aria-invalid={errors.description ? true : undefined}
              />
            </label>
            {errors.description && <p className="field-error" role="alert">{errors.description}</p>}
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span>05</span>
              <div>
                <h2>Evidence</h2>
                <p>Optional photo preview only — not uploaded or stored in this prototype phase.</p>
              </div>
            </div>
            <label className="evidence-label">
              Photo (optional)
              <input
                type="file"
                accept="image/*"
                onChange={e => handleEvidenceChange(e.target.files?.[0] ?? null)}
              />
            </label>
            {evidencePreview && (
              <img src={evidencePreview} alt="Selected evidence preview" className="evidence-preview" />
            )}
          </section>

          {submitError && <ErrorBanner message={submitError} />}
          <div className="form-footer">
            <p>
              Citizen-submitted reports are sent to the CrisisSim API for authority review in this
              prototype. Simulated emergency analysis is separate from your report.
            </p>
            <button type="submit" className="button button-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit report'}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}
