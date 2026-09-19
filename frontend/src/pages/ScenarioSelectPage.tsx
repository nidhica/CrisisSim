import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { Incident, ScenarioSummary } from '../types'
import { getScenarios } from '../services/scenarios'
import { getIncidents } from '../services/incidents'
import { Header } from '../components/layout/Header'
import { SeverityBadge } from '../components/common/SeverityBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { getRecentDemoScenarios } from '../services/demoScenarios'
import { hazardEmoji, hazardLabel } from '../constants/hazardDisplay'
import { incidentListLocationShort } from '../components/citizen/IncidentReportSummary'
import { IncidentStatusBadge } from '../components/citizen/IncidentStatusBadge'

export function ScenarioSelectPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [incidentsLoading, setIncidentsLoading] = useState(true)
  const [incidentsError, setIncidentsError] = useState<string | null>(null)
  const navigate = useNavigate()
  const recent = getRecentDemoScenarios()

  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch((e: unknown) => {
        const err = e as { message?: string }
        setError(err?.message || 'Failed to load scenarios')
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getIncidents()
      .then(setIncidents)
      .catch((e: unknown) =>
        setIncidentsError((e as Error).message || 'Failed to load incidents'),
      )
      .finally(() => setIncidentsLoading(false))
  }, [])

  const summary = useMemo(
    () => ({
      active: incidents.filter(item => item.status !== 'resolved').length,
      critical: incidents.filter(item => item.severity === 'critical').length,
      newReports: incidents.filter(item => item.status === 'reported').length,
      resolved: incidents.filter(item => item.status === 'resolved').length,
    }),
    [incidents],
  )

  return (
    <div className="app-shell ops-console flex flex-col">
      <Header />
      <main className="ops-personnel-page flex-1">
        <div className="w-full max-w-3xl mx-auto">
          <section className="incident-command-center">
            <div className="operations-intro ops-incident-command-header">
              <div>
                <p className="eyebrow section-kicker">INCIDENT COMMAND CENTER</p>
                <h1>Incident command center</h1>
                <p className="muted">
                  Incoming incidents, active simulations, and high-priority reports — prototype
                  authority workflow.
                </p>
              </div>
            </div>

            {incidentsLoading && (
              <div className="flex justify-center">
                <LoadingSpinner label="Loading incidents..." />
              </div>
            )}
            {incidentsError && <ErrorBanner message={incidentsError} />}

            {!incidentsLoading && !incidentsError && (
              <>
                <div className="incident-summary-grid">
                  <div className="content-card incident-summary-card">
                    <p className="section-kicker">ACTIVE</p>
                    <div className="incident-summary-value">{summary.active}</div>
                    <p className="muted">Incidents not resolved</p>
                  </div>
                  <div className="content-card incident-summary-card">
                    <p className="section-kicker">CRITICAL</p>
                    <div className="incident-summary-value">{summary.critical}</div>
                    <p className="muted">Critical severity</p>
                  </div>
                  <div className="content-card incident-summary-card">
                    <p className="section-kicker">NEW REPORTS</p>
                    <div className="incident-summary-value">{summary.newReports}</div>
                    <p className="muted">Status: reported</p>
                  </div>
                  <div className="content-card incident-summary-card">
                    <p className="section-kicker">RESOLVED</p>
                    <div className="incident-summary-value">{summary.resolved}</div>
                    <p className="muted">Closed incidents</p>
                  </div>
                </div>

                <section className="incoming-incidents">
                  <p className="eyebrow">INCOMING INCIDENTS</p>
                  <h2>Citizen crisis reports</h2>
                  {incidents.length === 0 ? (
                    <p className="muted">No citizen reports yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {incidents.map(incident => (
                        <div
                          key={incident.incident_id}
                          className={`recent-scenario incident-incoming-card content-card${
                            incident.severity === 'critical' || incident.severity === 'high'
                              ? ' ops-incident-critical'
                              : ''
                          }`}
                        >
                          <div className="incident-incoming-main">
                            <strong>{incident.incident_id}</strong>
                            <span>
                              {hazardEmoji(incident.hazard_type)}{' '}
                              {hazardLabel(incident.hazard_type)}
                            </span>
                            <span>{incidentListLocationShort(incident.location_name)}</span>
                            <span className="capitalize">{incident.severity}</span>
                            <IncidentStatusBadge status={incident.status} />
                            <span className="muted">
                              {new Date(incident.created_at).toLocaleString()}
                            </span>
                          </div>
                          <Link
                            to={`/personnel/incidents/${incident.incident_id}`}
                            className="incident-view-link"
                          >
                            View
                          </Link>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </>
            )}
          </section>

          <div className="operations-intro scenario-section-intro">
            <div>
              <p className="eyebrow">SIMULATION SCENARIOS</p>
              <h1>Active emergency scenarios</h1>
              <p>Select a scenario to review hazard conditions, test response plans and compare intervention strategies.</p>
            </div>
            <button onClick={() => navigate('/personnel/new')} className="button button-primary create-action">+ Create scenario</button>
          </div>

          {loading && <div className="flex justify-center"><LoadingSpinner label="Loading scenarios..." /></div>}
          {error && <ErrorBanner message={error} />}
          {!loading && !error && scenarios.length === 0 && (
            <ErrorBanner message="No scenarios are available. Start the local API and refresh this page." />
          )}

          <div className="space-y-3">
            {scenarios.map(s => (
              <button
                key={s.scenario_id}
                onClick={() => navigate(`/scenario/${s.scenario_id}`)}
                className="ops-scenario-card scenario-selection-card"
              >
                <div className="flex items-start justify-between mb-2">
                  <h2 className="font-semibold text-lg" style={{ color: '#f0f6fc' }}>
                    {s.name}
                  </h2>
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase tracking-wide muted">
                      {(s.hazard_type || 'flood').replaceAll('_', ' ')}
                    </span>
                    <SeverityBadge level={s.severity} size="md" />
                  </div>
                </div>
                <p className="text-sm muted leading-relaxed">{s.description}</p>
                <div className="mt-3 text-xs font-semibold" style={{ color: '#60a5fa' }}>
                  Open simulation →
                </div>
              </button>
            ))}
          </div>
          {recent.length > 0 && (
            <section className="recent-scenarios">
              <div>
                <p className="eyebrow">SESSION CONFIGURATIONS</p>
                <h2>Recent scenarios</h2>
              </div>
              <div className="space-y-3">
                {recent.map(item => (
                  <button
                    className="recent-scenario"
                    key={item.id}
                    onClick={() =>
                      navigate(`/scenario/${item.sourceScenarioId}?demo=${item.id}`)
                    }
                  >
                    <div>
                      <strong>{item.scenario.name}</strong>
                      <span>
                        {(item.scenario.hazard_type || 'flood').replaceAll('_', ' ')} · based on{' '}
                        {item.sourceScenarioId}
                      </span>
                    </div>
                    <SeverityBadge level={item.scenario.severity} />
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
