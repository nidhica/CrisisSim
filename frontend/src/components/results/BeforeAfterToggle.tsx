import { useState } from 'react'
import type { SimulationResult } from '../../types'

interface Props { result: SimulationResult }

export function BeforeAfterToggle({ result }: Props) {
  const [view, setView] = useState<'before' | 'after'>('before')

  const recommended = result.interventions.find(i => i.strategy === result.recommended_strategy)
  if (!recommended) return null

  const before = {
    avgRisk: result.baseline_zone_results.reduce((s, z) => s + z.risk_score, 0) / result.baseline_zone_results.length,
    avgRT: result.baseline_zone_results.reduce((s, z) => s + z.response_time_minutes, 0) / result.baseline_zone_results.length,
  }
  const after = {
    avgRisk: recommended.avg_risk_score,
    avgRT: recommended.avg_response_time_minutes,
  }

  const current = view === 'before' ? before : after
  const label = view === 'before' ? 'Baseline (current state)' : `After: ${recommended.label}`

  return (
    <div className="ops-before-after">
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button
          type="button"
          onClick={() => setView('before')}
          className={view === 'before' ? 'ops-run-button' : 'ops-secondary-button'}
        >
          Before
        </button>
        <button
          type="button"
          onClick={() => setView('after')}
          className={view === 'after' ? 'ops-run-button' : 'ops-secondary-button'}
        >
          After ({recommended.label})
        </button>
      </div>

      <div className="ops-before-after-panel">
        <h4>{label}</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
          <Metric label="Avg risk score" value={`${current.avgRisk.toFixed(1)} / 100`} highlight={view === 'after'} />
          <Metric label="Avg response time" value={`${current.avgRT.toFixed(1)} min`} highlight={view === 'after'} />
          {view === 'after' && (
            <>
              <Metric label="Risk reduction" value={`-${recommended.risk_reduction_pct.toFixed(1)}%`} good />
              <Metric
                label="Response-time improvement"
                value={`-${recommended.response_time_improvement_minutes.toFixed(1)} min`}
                good
              />
            </>
          )}
        </div>

        <div style={{ marginTop: 16 }}>
          <h5>Zone results</h5>
          <div>
            {(view === 'before' ? result.baseline_zone_results : recommended.zone_results).map(zr => (
              <div key={zr.zone_id} className="ops-ranking-row">
                <span className="muted">{zr.zone_id}</span>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <span style={{ fontFamily: 'monospace' }}>Risk: {zr.risk_score.toFixed(1)}</span>
                  <SeverityPill level={zr.risk_level} />
                  <span className="muted" style={{ fontFamily: 'monospace' }}>
                    {zr.response_time_minutes.toFixed(0)}m
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SeverityPill({ level }: { level: string }) {
  const className = `ops-risk-pill risk-${level}`
  return <span className={className}>{level}</span>
}

function Metric({ label, value, highlight, good }: { label: string; value: string; highlight?: boolean; good?: boolean }) {
  return (
    <div className="ops-metric-block">
      <div className="ops-metric-block-label">{label}</div>
      <div
        className={`ops-metric-block-value${good ? ' is-good' : ''}${highlight && !good ? ' is-highlight' : ''}`}
      >
        {value}
      </div>
    </div>
  )
}
