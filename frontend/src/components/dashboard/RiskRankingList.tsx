import { useState } from 'react'
import type { ZoneResult } from '../../types'
import { SeverityBadge } from '../common/SeverityBadge'

interface Props { zoneResults: ZoneResult[] }

export function RiskRankingList({ zoneResults }: Props) {
  const [sortBy, setSortBy] = useState<'risk' | 'response'>('risk')
  const sorted = [...zoneResults].sort((a, b) =>
    sortBy === 'risk'
      ? b.risk_score - a.risk_score
      : b.response_time_minutes - a.response_time_minutes
  )

  return (
    <div className="content-card ops-panel risk-ranking-panel">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <p className="section-kicker" style={{ margin: 0 }}>ZONE RANKING</p>
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            type="button"
            onClick={() => setSortBy('risk')}
            className={`ops-chip-toggle${sortBy === 'risk' ? ' is-active' : ''}`}
          >
            Risk
          </button>
          <button
            type="button"
            onClick={() => setSortBy('response')}
            className={`ops-chip-toggle${sortBy === 'response' ? ' is-active' : ''}`}
          >
            Response
          </button>
        </div>
      </div>
      <div>
        {sorted.map((zr, idx) => (
          <div key={zr.zone_id} className="ops-ranking-row">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="muted" style={{ width: 16 }}>{idx + 1}</span>
              <span style={{ fontWeight: 600 }}>{zr.zone_id}</span>
              <SeverityBadge level={zr.risk_level} />
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 800 }}>{zr.risk_score.toFixed(1)}</div>
              <div className="muted">{zr.response_time_minutes.toFixed(0)}m</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
