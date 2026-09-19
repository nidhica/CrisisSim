import type { InterventionResult } from '../../types'

interface Props {
  recommended: InterventionResult | null
  recommendedStrategy: string
}

export function StrategyRecommendationCard({ recommended, recommendedStrategy }: Props) {
  if (!recommended) {
    return (
      <section className="ops-strategy-card content-card" aria-label="Strategy recommendation">
        <p className="section-kicker">STRATEGY RECOMMENDATION</p>
        <p className="muted">Run a simulation to see the recommended intervention.</p>
      </section>
    )
  }

  return (
    <section className="ops-strategy-card content-card" aria-label="Strategy recommendation">
      <p className="section-kicker">STRATEGY RECOMMENDATION</p>
      <p className="ops-strategy-card-label">★ Recommended</p>
      <h3 className="ops-strategy-card-title">{recommended.label}</h3>
      <dl className="ops-strategy-card-metrics">
        <div>
          <dt>Avg risk</dt>
          <dd>{recommended.avg_risk_score.toFixed(1)}</dd>
        </div>
        <div>
          <dt>Avg response</dt>
          <dd>{recommended.avg_response_time_minutes.toFixed(1)} min</dd>
        </div>
        <div>
          <dt>Risk reduction</dt>
          <dd>{recommended.risk_reduction_pct.toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Composite score</dt>
          <dd>{recommended.composite_score.toFixed(4)}</dd>
        </div>
      </dl>
      <p className="muted" style={{ fontSize: '11px', marginTop: 12 }}>
        Engine strategy key: {recommendedStrategy.replaceAll('_', ' ')}
      </p>
    </section>
  )
}
