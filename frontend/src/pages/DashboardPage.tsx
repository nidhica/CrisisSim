import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useScenario } from '../context/ScenarioContext'
import { useSimulation } from '../context/SimulationContext'
import { Header } from '../components/layout/Header'
import { SituationSummaryRail } from '../components/dashboard/SituationSummaryRail'
import { RiskRankingList } from '../components/dashboard/RiskRankingList'
import { CommandBrief } from '../components/dashboard/CommandBrief'
import { ResponseAnalysisPanel } from '../components/dashboard/ResponseAnalysisPanel'
import { OperationsConsoleHeader } from '../components/dashboard/OperationsConsoleHeader'
import { SimMap } from '../components/map/SimMap'
import { WhatIfPanel } from '../components/simulator/WhatIfPanel'
import { ComparisonTable } from '../components/results/ComparisonTable'
import { ProjectedImpact } from '../components/results/ProjectedImpact'
import { StrategyRecommendationCard } from '../components/results/StrategyRecommendationCard'
import { BeforeAfterToggle } from '../components/results/BeforeAfterToggle'
import { AIExplanation } from '../components/results/AIExplanation'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { getDemoScenario } from '../services/demoScenarios'
import type { HazardType } from '../types'

type ResultTab = 'comparison' | 'beforeafter' | 'explain' | 'ranking'

const HAZARD_LABELS: Record<HazardType, string> = {
  flood: 'Flood',
  fire: 'Fire',
  earthquake: 'Earthquake',
  cyclone: 'Cyclone / Severe Storm',
  industrial_accident: 'Industrial Accident',
}

export function DashboardPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { scenario, loading: scenarioLoading, error: scenarioError, loadScenario } = useScenario()
  const { simulationResult, isRunning, initDraftParams } = useSimulation()
  const [activeTab, setActiveTab] = useState<ResultTab>('comparison')
  const [demoWarning, setDemoWarning] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      const demoId = searchParams.get('demo')
      const demo = demoId ? getDemoScenario(demoId) : null
      if (demoId && (!demo || demo.sourceScenarioId !== id)) {
        setDemoWarning(
          'The requested session configuration was not found. Showing the base scenario instead.',
        )
        loadScenario(id, null)
      } else {
        setDemoWarning(null)
        loadScenario(id, demo?.sourceScenarioId === id ? demo.scenario : null)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, searchParams])

  useEffect(() => {
    if (scenario) initDraftParams(scenario)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario])

  if (scenarioLoading) {
    return (
      <div className="app-shell ops-console flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner label="Loading scenario..." />
        </div>
      </div>
    )
  }

  if (scenarioError || !scenario) {
    return (
      <div className="app-shell ops-console flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-3">
            <ErrorBanner message={scenarioError || 'Scenario not found'} />
            <button type="button" onClick={() => navigate('/personnel')} className="ops-link-muted">
              ← Back to scenarios
            </button>
          </div>
        </div>
      </div>
    )
  }

  const zoneResults = simulationResult?.baseline_zone_results ?? []
  const hazard = (simulationResult?.hazard_type || scenario.hazard_type || 'flood') as HazardType
  const hazardLabel = HAZARD_LABELS[hazard]
  const baseline =
    simulationResult?.interventions.find(iv => iv.strategy === 'baseline') ?? null
  const recommended =
    simulationResult?.interventions.find(
      iv => iv.strategy === simulationResult.recommended_strategy,
    ) ?? null

  const incidentPin =
    scenario.latitude != null && scenario.longitude != null && scenario.source_incident_id
      ? {
          latitude: scenario.latitude,
          longitude: scenario.longitude,
          label: scenario.location_name || 'Reported location',
        }
      : undefined

  return (
    <div className={`app-shell ops-console ops-dashboard hazard-theme-${hazard}`}>
      <Header scenario={scenario} />

      <div className="ops-dashboard-frame">
        <SituationSummaryRail
          scenario={scenario}
          result={simulationResult}
          isRunning={isRunning}
        />

        <div className="ops-dashboard-main">
          <OperationsConsoleHeader
            scenario={scenario}
            result={simulationResult}
            isRunning={isRunning}
          />

          {demoWarning && <ErrorBanner message={demoWarning} />}

          <CommandBrief scenario={scenario} result={simulationResult} isRunning={isRunning} />

          <section className="ops-operations-split" aria-label="Operational map and response analysis">
            <div className="ops-map-column">
              <header className="ops-map-column-header">
                <div>
                  <p className="section-kicker">OPERATIONAL MAP</p>
                  <h2>{hazardLabel} · simulated zones</h2>
                </div>
                <span className="muted ops-map-column-meta">
                  Real geography · simulated conditions
                  {scenario.source_incident_id ? ' · citizen report' : ''}
                </span>
              </header>
              <div className="ops-map-stage">
                <div className="ops-map-badge">
                  <strong>SIMULATION MAP</strong>
                  <span>Real geography · simulated conditions</span>
                </div>
                <SimMap
                  scenario={scenario}
                  zoneResults={zoneResults}
                  result={simulationResult}
                  incidentPin={incidentPin}
                />
              </div>
            </div>

            <ResponseAnalysisPanel
              scenario={scenario}
              result={simulationResult}
              isRunning={isRunning}
            />
          </section>

          <section className="ops-whatif-section" aria-label="What-if simulator">
            <WhatIfPanel scenario={scenario} />
          </section>

          {simulationResult && (
            <section className="ops-impact-split" aria-label="Projected impact and recommendation">
              <ProjectedImpact baseline={baseline} recommended={recommended} />
              <StrategyRecommendationCard
                recommended={recommended}
                recommendedStrategy={simulationResult.recommended_strategy}
              />
            </section>
          )}

          {simulationResult && (
            <section className="ops-detailed-results ops-results-panel" aria-label="Detailed simulation results">
              <header className="ops-detailed-results-header">
                <div>
                  <p className="section-kicker">DETAILED RESULTS</p>
                  <h2>Strategy comparison &amp; analysis</h2>
                </div>
                <p className="muted" style={{ fontSize: '12px' }}>
                  Deterministic simulation · {hazardLabel}
                </p>
              </header>

              <div
                className="ops-results-tabs flex flex-wrap gap-2 mb-4 pb-3"
                style={{ borderBottom: '1px solid #243447' }}
              >
                {(
                  [
                    ['comparison', 'Strategy comparison'],
                    ['ranking', 'Zone ranking'],
                    ['beforeafter', 'Before vs after'],
                    ['explain', 'Explanation'],
                  ] as [ResultTab, string][]
                ).map(([tab, label]) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={activeTab === tab ? 'ops-run-button' : 'ops-secondary-button'}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {activeTab === 'comparison' && (
                <ComparisonTable
                  interventions={simulationResult.interventions}
                  recommendedStrategy={simulationResult.recommended_strategy}
                  hazardLabel={hazardLabel}
                  includeProjectedImpact={false}
                />
              )}
              {activeTab === 'ranking' && <RiskRankingList zoneResults={zoneResults} />}
              {activeTab === 'beforeafter' && <BeforeAfterToggle result={simulationResult} />}
              {activeTab === 'explain' && <AIExplanation />}
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
