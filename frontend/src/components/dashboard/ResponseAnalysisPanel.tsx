import type { Scenario, SimulationResult } from '../../types'
import {
  averageBaselineResponseTime,
  buildWhyRecommendation,
  findRecommendedIntervention,
  highestRiskZone,
  primaryBottleneck,
} from '../../utils/commandBriefUtils'

interface Props {
  scenario: Scenario
  result: SimulationResult | null
  isRunning: boolean
}

export function ResponseAnalysisPanel({ scenario, result, isRunning }: Props) {
  if (!result || isRunning) {
    return (
      <aside className="ops-analysis-panel" aria-label="Response analysis">
        <p className="section-kicker">RESPONSE ANALYSIS</p>
        <h3 className="ops-analysis-panel-title">Awaiting simulation</h3>
        <p className="muted">
          Run the What-If simulator to generate recommended strategies, bottleneck analysis, and
          projected response times.
        </p>
      </aside>
    )
  }

  const recommended = findRecommendedIntervention(result)
  const bottleneck = primaryBottleneck(result)
  const topZone = highestRiskZone(result, scenario)
  const why = buildWhyRecommendation(bottleneck, recommended)
  const avgRt = averageBaselineResponseTime(result)
  const statusLabel = isRunning ? 'Running' : 'Completed'

  return (
    <aside className="ops-analysis-panel" aria-label="Response analysis">
      <p className="section-kicker">RESPONSE ANALYSIS</p>

      <section className="ops-analysis-block">
        <p className="command-brief-label">Recommended strategy</p>
        <p className="ops-analysis-highlight">{recommended?.label ?? '—'}</p>
      </section>

      {why && (
        <section className="ops-analysis-block">
          <p className="command-brief-label">Why?</p>
          <p className="muted ops-analysis-why">{why}</p>
        </section>
      )}

      <section className="ops-analysis-block">
        <p className="command-brief-label">Primary bottleneck</p>
        {topZone && <p className="ops-analysis-zone">{topZone.zoneName}</p>}
        <p className="ops-analysis-value">{bottleneck?.description ?? 'No critical bottleneck flagged'}</p>
      </section>

      <section className="ops-analysis-block">
        <p className="command-brief-label">Projected response</p>
        <p className="ops-metric-value" style={{ fontSize: '28px' }}>
          {avgRt != null ? `${avgRt.toFixed(1)} min` : '—'}
        </p>
        <p className="muted" style={{ fontSize: '11px' }}>Baseline average across simulated zones</p>
      </section>

      <section className="ops-analysis-block ops-analysis-status">
        <p className="command-brief-label">Simulation status</p>
        <p className="ops-analysis-status-value">{statusLabel}</p>
        {result.run_at && (
          <p className="muted" style={{ fontSize: '11px', marginTop: 6 }}>
            {new Date(result.run_at).toLocaleString()}
          </p>
        )}
      </section>

      <p className="ops-analysis-footnote muted">
        Results are deterministic prototype projections — not real-world emergency directives.
      </p>
    </aside>
  )
}
