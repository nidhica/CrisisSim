import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getScenario, getScenarios } from '../services/scenarios'
import type { Scenario, ScenarioSummary } from '../types'
import { Header } from '../components/layout/Header'
import { SimMap } from '../components/map/SimMap'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { SeverityBadge } from '../components/common/SeverityBadge'
import { getIncidents } from '../services/incidents'
import type { Incident } from '../types'
import { hazardEmoji, hazardLabel as incidentHazardLabel } from '../constants/hazardDisplay'
import { incidentListLocationShort } from '../components/citizen/IncidentReportSummary'
import { IncidentStatusBadge } from '../components/citizen/IncidentStatusBadge'

export function CitizenDashboardPage() {
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reports, setReports] = useState<Incident[]>([])
  const [reportsLoading, setReportsLoading] = useState(true)
  const [reportsError, setReportsError] = useState<string | null>(null)
  useEffect(() => { getScenarios().then((items: ScenarioSummary[]) => items[0]).then(item => item ? getScenario(item.scenario_id) : Promise.reject(new Error('No emergency scenario is available'))).then(setScenario).catch((e: unknown) => setError((e as Error).message)) }, [])
  useEffect(() => {
    getIncidents()
      .then(setReports)
      .catch((e: unknown) => setReportsError((e as Error).message || 'Could not load your reports.'))
      .finally(() => setReportsLoading(false))
  }, [])
  if (error) return <div className="app-shell"><Header mode="citizen" /><main className="page-center"><ErrorBanner message={error} /></main></div>
  if (!scenario) return <div className="app-shell"><Header mode="citizen" /><main className="page-center"><LoadingSpinner label="Loading emergency information..." /></main></div>
  const shelterCapacity = scenario.shelters.reduce((sum, shelter) => sum + shelter.capacity, 0)
  const shelterOccupancy = scenario.shelters.reduce((sum, shelter) => sum + shelter.current_occupancy, 0)
  const hazardLabel = (scenario.hazard_type || 'flood').replaceAll('_', ' ')
  const safetyTips: Record<string, string[]> = {
    flood: [
      'Move to higher ground if authorities issue an evacuation notice.',
      'Do not walk or drive through flood water.',
      'Keep emergency numbers, medication and essential documents ready.',
      'Use official alerts for local instructions and updates.',
    ],
    fire: [
      'Follow official evacuation routes and avoid smoke-filled areas.',
      'Close windows and doors if told to shelter in place.',
      'Keep medication and essential documents ready to leave quickly.',
      'Use official alerts for local instructions and updates.',
    ],
    earthquake: [
      'Drop, cover, and hold on during shaking; move outside only when safe.',
      'Expect aftershocks and avoid damaged buildings.',
      'Keep medication and essential documents ready.',
      'Use official alerts for local instructions and updates.',
    ],
    cyclone: [
      'Follow evacuation notices early; stay away from coastal surge zones.',
      'Secure loose outdoor items and prepare for power outages.',
      'Keep medication, water, and essential documents ready.',
      'Use official alerts for local instructions and updates.',
    ],
    industrial_accident: [
      'Move upwind and away from the reported release area if instructed.',
      'Shelter indoors with windows closed if told to shelter in place.',
      'Keep medication and essential documents ready.',
      'Use official alerts for local instructions and updates.',
    ],
  }
  const tips = safetyTips[scenario.hazard_type] || safetyTips.flood
  return <div className="app-shell citizen-shell citizen-shell-premium"><Header mode="citizen" scenario={scenario} /><main className="citizen-content">
    <section className="citizen-hero-banner content-card">
      <p className="section-kicker">CITIZEN DASHBOARD</p>
      <h1 style={{ margin: '0 0 8px', fontSize: 'clamp(28px, 4vw, 40px)' }}>Report a crisis</h1>
      <p className="muted">Help emergency authorities understand where support may be needed — prototype reporting with real geography.</p>
    </section>
    <section className="citizen-actions-grid">
      <Link to="/citizen/report" className="report-crisis-card">
        <span className="report-crisis-emoji" aria-hidden>🚨</span>
        <div>
          <p className="section-kicker">QUICK ACTION</p>
          <h2>Report a Crisis</h2>
          <p className="muted">Submit hazard, location, and severity for authority review.</p>
        </div>
      </Link>
      <section className="content-card my-reports-card">
        <p className="section-kicker">MY REPORTS</p>
        <h2>Submitted incident reports</h2>
        {reportsLoading && <LoadingSpinner label="Loading your reports..." />}
        {reportsError && <ErrorBanner message={reportsError} />}
        {!reportsLoading && !reportsError && reports.length === 0 ? (
          <p className="muted">No reports yet. Use Report a Crisis to submit your first prototype report.</p>
        ) : null}
        {!reportsLoading && !reportsError && reports.length > 0 ? (
          <ul className="incident-list">
            {reports.map(report => (
              <li key={report.incident_id} className="incident-list-item">
                <div className="incident-list-main">
                  <strong>{report.incident_id}</strong>
                  <span>{hazardEmoji(report.hazard_type)} {incidentHazardLabel(report.hazard_type)}</span>
                  <span>{incidentListLocationShort(report.location_name)}</span>
                  <span className="capitalize">{report.severity}</span>
                  <IncidentStatusBadge status={report.status} />
                </div>
                <Link to={`/citizen/reports/${report.incident_id}`} className="incident-view-link">View report</Link>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </section>
    <section className="citizen-alert"><div><p className="eyebrow">CURRENT EMERGENCY STATUS</p><h1>{scenario.name}</h1><p>{scenario.description}</p><p className="muted capitalize">Hazard: {hazardLabel}</p></div><SeverityBadge level={scenario.severity} size="md" /></section>
    <div className="citizen-grid"><section className="content-card map-card"><div className="section-heading"><div><p className="section-kicker">SCENARIO OVERVIEW</p><h2>Emergency area map</h2></div><span className="map-note">Select a zone for details</span></div><div className="citizen-map"><SimMap scenario={scenario} zoneResults={[]} result={null} /></div></section>
      <aside className="citizen-aside"><section className="content-card"><p className="section-kicker">SAFE PLACES</p><h2>Available shelter space</h2><div className="capacity-number">{Math.max(shelterCapacity - shelterOccupancy, 0).toLocaleString()} <span>spaces</span></div><p className="muted">{shelterOccupancy.toLocaleString()} of {shelterCapacity.toLocaleString()} shelter places currently in use.</p></section><section className="content-card"><p className="section-kicker">EMERGENCY SERVICES</p><h2>Hospital availability</h2>{scenario.hospitals.map(hospital => <div className="facility-row" key={hospital.hospital_id}><div><strong>{hospital.name}</strong><small>Emergency care facility</small></div><span>{hospital.current_occupancy}/{hospital.capacity + hospital.surge_capacity}</span></div>)}</section></aside></div>
    <div className="citizen-info-grid"><section className="content-card"><p className="section-kicker">SHELTERS</p><h2>Scenario shelter information</h2>{scenario.shelters.map(shelter => <div className="facility-row" key={shelter.shelter_id}><div><strong>{shelter.name}</strong><small>Capacity: {shelter.capacity}</small></div><span>{shelter.current_occupancy} in use</span></div>)}</section><section className="content-card"><p className="section-kicker">SAFETY GUIDANCE</p><h2>Stay safe during this emergency</h2><ul className="safety-list">{tips.map(tip => <li key={tip}>{tip}</li>)}</ul></section><section className="content-card"><p className="section-kicker">COMMUNITY NOTICE</p><h2>About this information</h2><p className="muted">This dashboard shows a demonstration emergency scenario, not your live location. Follow local emergency services for location-specific directions. CrisisSim is a hackathon prototype, not a real emergency-control system.</p></section></div>
  </main></div>
}
