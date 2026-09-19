import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import type { Incident, IncidentStatus } from '../types'
import { getIncident, updateIncident } from '../services/incidents'
import { getScenarios } from '../services/scenarios'
import {
  ScenarioFromIncidentError,
  createDemoScenarioFromIncident,
} from '../services/createScenarioFromIncident'
import { Header } from '../components/layout/Header'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { SeverityBadge } from '../components/common/SeverityBadge'
import { IncidentStatusBadge } from '../components/citizen/IncidentStatusBadge'
import { hazardLabel } from '../constants/hazardDisplay'
import { IncidentLocationMap } from '../components/map/IncidentLocationMap'
import { IncidentResponseTimeline } from '../components/citizen/IncidentResponseTimeline'
import { getRecentDemoScenarios } from '../services/demoScenarios'

const NEXT_ACTION: Partial<
  Record<Incident['status'], { label: string; next: IncidentStatus }>
> = {
  reported: { label: 'Acknowledge incident', next: 'acknowledged' },
  acknowledged: { label: 'Start assessment', next: 'assessing' },
  assessing: { label: 'Mark response dispatched', next: 'response_dispatched' },
  response_dispatched: { label: 'Mark resolved', next: 'resolved' },
}

export function PersonnelIncidentDetailPage() {
  const navigate = useNavigate()
  const { incidentId } = useParams<{ incidentId: string }>()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [simulateError, setSimulateError] = useState<string | null>(null)
  const [simulationCreated, setSimulationCreated] = useState(false)

  const load = useCallback(async () => {
    if (!incidentId) return
    setLoading(true)
    setError(null)
    try {
      const data = await getIncident(incidentId)
      setIncident(data)
      if (!data) {
        setError('Incident not found.')
      }
    } catch (e: unknown) {
      setError((e as Error).message || 'Failed to load incident.')
    } finally {
      setLoading(false)
    }
  }, [incidentId])

  useEffect(() => {
    load()
  }, [load])

  async function advanceStatus() {
    if (!incident) return
    const action = NEXT_ACTION[incident.status]
    if (!action) return
    setUpdating(true)
    setActionError(null)
    try {
      const updated = await updateIncident(incident.incident_id, action.next)
      setIncident(updated)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setActionError(err.response?.data?.detail || err.message || 'Status update failed.')
    } finally {
      setUpdating(false)
    }
  }

  async function simulateResponse() {
    if (!incident) return
    setSimulating(true)
    setSimulateError(null)
    try {
      const summaries = await getScenarios()
      const demo = await createDemoScenarioFromIncident(incident, summaries)
      setSimulationCreated(true)
      navigate(`/scenario/${demo.sourceScenarioId}?demo=${demo.id}`)
    } catch (e: unknown) {
      if (e instanceof ScenarioFromIncidentError) {
        setSimulateError(e.message)
      } else {
        setSimulateError((e as Error).message || 'Could not create simulation from this incident.')
      }
    } finally {
      setSimulating(false)
    }
  }

  const action = incident ? NEXT_ACTION[incident.status] : null
  const canSimulate =
    incident?.status === 'acknowledged' || incident?.status === 'assessing'

  if (loading) {
    return (
      <div className="app-shell ops-console">
        <Header />
        <main className="page-center">
          <LoadingSpinner label="Loading incident..." />
        </main>
      </div>
    )
  }

  if (error || !incident) {
    return (
      <div className="app-shell ops-console">
        <Header />
        <main className="page-center">
          <ErrorBanner message={error || 'Incident not found.'} />
          <Link to="/personnel" className="button button-primary">Back to operations</Link>
        </main>
      </div>
    )
  }

  const created = new Date(incident.created_at).toLocaleString()
  const simulationLinked = getRecentDemoScenarios().some(
    item => item.scenario.source_incident_id === incident.incident_id,
  )

  return (
    <div className={`app-shell ops-console hazard-theme-${incident.hazard_type}`}>
      <Header />
      <main className="ops-personnel-page ops-incident-command">
        <header className="ops-incident-command-header">
          <div>
            <p className="section-kicker">INCIDENT COMMAND</p>
            <h1>INCIDENT {incident.incident_id}</h1>
            <p className="ops-incident-hazard-line">
              <SeverityBadge level={incident.severity} size="md" />
              <strong>{hazardLabel(incident.hazard_type)}</strong>
            </p>
            <p className="muted">📍 {incident.location_name}</p>
          </div>
          <Link to="/personnel" className="text-button">Back to operations</Link>
        </header>

        <div className="ops-incident-cta-bar content-card">
          {incident.status === 'reported' && (
            <p className="muted">Acknowledge the incident before running a simulation.</p>
          )}
          {canSimulate && (
            <button
              type="button"
              className="button button-primary simulate-response-button ops-simulate-cta ops-simulate-cta-dominant"
              disabled={simulating}
              onClick={simulateResponse}
            >
              {simulating ? 'Creating simulation…' : '⚡ Simulate Response'}
            </button>
          )}
          {action && (
            <button
              type="button"
              className="button button-secondary"
              disabled={updating}
              onClick={advanceStatus}
            >
              {updating ? 'Updating…' : action.label.toUpperCase()}
            </button>
          )}
          {simulateError && <ErrorBanner message={simulateError} />}
          {actionError && <ErrorBanner message={actionError} />}
        </div>

        <section className="content-card ops-incident-timeline-card">
          <p className="section-kicker">INCIDENT TIMELINE</p>
          <IncidentResponseTimeline
            incident={incident}
            simulationLinked={simulationLinked}
            simulationCreatedThisSession={simulationCreated}
            layout="vertical"
          />
        </section>

        <div className="ops-incident-detail-grid">
          <section className="content-card">
            <p className="section-kicker">REPORTED LOCATION</p>
            <p className="muted">Citizen-selected coordinates — not simulated hazard boundaries.</p>
            <IncidentLocationMap
              latitude={incident.latitude}
              longitude={incident.longitude}
              locationName={incident.location_name}
            />
          </section>

          <section className="content-card">
            <p className="section-kicker">INCIDENT DETAILS</p>
            <p>
              Status: <IncidentStatusBadge status={incident.status} />
            </p>
            <p className="muted">Reported: {created}</p>
            <div className="report-description-block">
              <strong>Description</strong>
              <p>{incident.description}</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
