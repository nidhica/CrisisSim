import type { InterventionResult } from '../../types'
import { percentChange } from '../../utils/commandBriefUtils'

interface Props {
  baseline: InterventionResult | null
  recommended: InterventionResult | null
}

export function ProjectedImpact({ baseline, recommended }: Props) {
  if (!baseline || !recommended || baseline.strategy === recommended.strategy) {
    return null
  }

  const riskPct = percentChange(baseline.avg_risk_score, recommended.avg_risk_score)
  const rtPct = percentChange(baseline.avg_response_time_minutes, recommended.avg_response_time_minutes)

  return (
    <section className="projected-impact content-card ops-panel" aria-label="Projected impact">
      <span className="projected-tag">Projected · simulation only</span>
      <p className="section-kicker">PROJECTED IMPACT</p>
      <p className="muted projected-impact-note">
        Baseline vs recommended strategy from deterministic simulation outputs — not a real-world
        forecast.
      </p>

      <div className="projected-impact-visual">
        <div className="projected-impact-side">
          <p className="command-brief-label">Baseline</p>
          <p className="projected-impact-big">{baseline.avg_risk_score.toFixed(1)}</p>
          <p className="muted">Avg risk</p>
          <p className="projected-impact-big">{baseline.avg_response_time_minutes.toFixed(1)} min</p>
          <p className="muted">Avg response time</p>
        </div>
        <div className="projected-impact-arrow" aria-hidden>→</div>
        <div className="projected-impact-side recommended">
          <p className="command-brief-label">Recommended</p>
          <p className="muted">{recommended.label}</p>
          <p className="projected-impact-big">{recommended.avg_risk_score.toFixed(1)}</p>
          <p className="muted">
            Avg risk{riskPct != null && riskPct < 0 ? ` ↓ ${Math.abs(riskPct).toFixed(1)}%` : ''}
          </p>
          <p className="projected-impact-big">{recommended.avg_response_time_minutes.toFixed(1)} min</p>
          <p className="muted">
            Response time
            {rtPct != null && rtPct < 0 ? ` ↓ ${Math.abs(rtPct).toFixed(1)}%` : ''}
          </p>
        </div>
      </div>

      <div className="projected-impact-deltas">
        <div className={riskPct != null && riskPct < 0 ? 'delta-good' : 'delta-neutral'}>
          <span className="command-brief-label">Risk improvement</span>
          <span>{baseline.avg_risk_score.toFixed(1)} → {recommended.avg_risk_score.toFixed(1)}</span>
        </div>
        <div className={rtPct != null && rtPct < 0 ? 'delta-good' : 'delta-neutral'}>
          <span className="command-brief-label">Response-time improvement</span>
          <span>
            {baseline.avg_response_time_minutes.toFixed(1)} min →{' '}
            {recommended.avg_response_time_minutes.toFixed(1)} min
          </span>
        </div>
      </div>
    </section>
  )
}
