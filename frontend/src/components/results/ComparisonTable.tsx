import type { InterventionResult } from '../../types'
import { ProjectedImpact } from './ProjectedImpact'

interface Props {
  interventions: InterventionResult[]
  recommendedStrategy: string
  hazardLabel?: string
  includeProjectedImpact?: boolean
}

export function ComparisonTable({
  interventions,
  recommendedStrategy,
  hazardLabel,
  includeProjectedImpact = true,
}: Props) {
  const ordered = ['baseline', 'resource_reallocation', 'capacity_expansion', 'combined']
  const sorted = [...interventions].sort((a, b) => ordered.indexOf(a.strategy) - ordered.indexOf(b.strategy))
  const baseline = interventions.find(iv => iv.strategy === 'baseline') ?? null
  const recommended = interventions.find(iv => iv.strategy === recommendedStrategy) ?? null

  return (
    <div className="overflow-x-auto">
      {includeProjectedImpact && <ProjectedImpact baseline={baseline} recommended={recommended} />}
      {hazardLabel && (
        <p className="muted" style={{ fontSize: '12px', marginBottom: 12 }}>
          Intervention comparison for <strong style={{ color: '#e2e8f0' }}>{hazardLabel}</strong>
        </p>
      )}
      <table className="ops-table">
        <thead>
          <tr>
            <th>Strategy</th>
            <th style={{ textAlign: 'right' }}>Avg Risk</th>
            <th style={{ textAlign: 'right' }}>Risk Reduction</th>
            <th style={{ textAlign: 'right' }}>Avg RT (min)</th>
            <th style={{ textAlign: 'right' }}>RT Improvement</th>
            <th style={{ textAlign: 'right' }}>Bottleneck Res.</th>
            <th style={{ textAlign: 'right' }}>Cost</th>
            <th style={{ textAlign: 'right' }}>Score</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(iv => {
            const isRec = iv.strategy === recommendedStrategy
            return (
              <tr key={iv.strategy} className={isRec ? 'ops-row-recommended' : undefined}>
                <td>
                  <div className="flex items-center gap-2">
                    {isRec && <span title="Recommended" style={{ color: '#60a5fa' }}>★</span>}
                    <span className={isRec ? 'font-semibold' : ''} style={{ color: isRec ? '#93c5fd' : '#e2e8f0' }}>
                      {iv.label}
                    </span>
                    {isRec && (
                      <span
                        style={{
                          background: 'rgb(59 130 246 / 20%)',
                          color: '#93c5fd',
                          fontSize: '10px',
                          padding: '2px 8px',
                          borderRadius: '999px',
                          fontWeight: 700,
                        }}
                      >
                        RECOMMENDED
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{iv.avg_risk_score.toFixed(1)}</td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace', color: '#4ade80' }}>
                  {iv.risk_reduction_pct.toFixed(1)}%
                </td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{iv.avg_response_time_minutes.toFixed(1)}</td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace', color: '#4ade80' }}>
                  {iv.response_time_improvement_minutes.toFixed(1)}
                </td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{iv.bottleneck_resolution_score.toFixed(2)}</td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{iv.resource_cost}</td>
                <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: '#60a5fa' }}>
                  {iv.composite_score.toFixed(4)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
