import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Header } from '../components/layout/Header'
import { IncidentReportSummary } from '../components/citizen/IncidentReportSummary'
import { getIncident } from '../services/incidents'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import type { Incident } from '../types'

export function IncidentDetailPage() {
  const { incidentId } = useParams<{ incidentId: string }>()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!incidentId) {
      setLoading(false)
      setError('Missing incident ID.')
      return
    }
    setLoading(true)
    getIncident(incidentId)
      .then(data => {
        setIncident(data)
        if (!data) {
          setError('Report not found.')
        }
      })
      .catch((e: unknown) => setError((e as Error).message || 'Failed to load report.'))
      .finally(() => setLoading(false))
  }, [incidentId])

  if (loading) {
    return (
      <div className="app-shell">
        <Header mode="citizen" />
        <main className="page-center">
          <LoadingSpinner label="Loading report..." />
        </main>
      </div>
    )
  }

  if (error || !incident) {
    return (
      <div className="app-shell">
        <Header mode="citizen" />
        <main className="page-center">
          <ErrorBanner message={error || 'Report not found.'} />
          <Link to="/citizen" className="button button-primary">Back to dashboard</Link>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Header mode="citizen" />
      <main className="create-page">
        <div className="create-heading">
          <div>
            <p className="eyebrow">MY REPORTS</p>
            <h1>{incident.incident_id}</h1>
          </div>
          <Link to="/citizen" className="text-button">Back to dashboard</Link>
        </div>
        <IncidentReportSummary incident={incident} title="Citizen crisis report" />
        <p className="muted report-description-block">
          <strong>Description</strong>
          <br />
          {incident.description}
        </p>
      </main>
    </div>
  )
}
