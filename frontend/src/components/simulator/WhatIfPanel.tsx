import type { Scenario } from '../../types'
import { useSimulation } from '../../context/SimulationContext'
import { ZoneParameterRow } from './ZoneParameterRow'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { ErrorBanner } from '../common/ErrorBanner'

interface Props { scenario: Scenario }

export function WhatIfPanel({ scenario }: Props) {
  const { draftParams, isRunning, error, runSim, resetParams } = useSimulation()

  return (
    <div className="ops-whatif ops-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 12 }}>
        <div>
          <p className="section-kicker">WHAT-IF SIMULATOR</p>
          <h2>Explore scenario assumptions</h2>
          <p className="muted" style={{ margin: '6px 0 0', fontSize: '13px' }}>
            Explore how changing scenario assumptions affects the projected response.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button
            type="button"
            onClick={() => resetParams(scenario)}
            disabled={isRunning}
            className="ops-secondary-button"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={runSim}
            disabled={isRunning || draftParams.length === 0}
            className="ops-run-button"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            {isRunning ? (
              <>
                <LoadingSpinner label="" />
                <span>Running…</span>
              </>
            ) : (
              '▶ Run Simulation'
            )}
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <div style={{ maxHeight: '240px', overflowY: 'auto', paddingRight: 4 }}>
        {draftParams.map(param => {
          const zone = scenario.zones.find(z => z.zone_id === param.zone_id)
          return zone ? (
            <ZoneParameterRow
              key={param.zone_id}
              zone={zone}
              params={param}
              hazardType={scenario.hazard_type}
            />
          ) : null
        })}
      </div>
      <p className="muted" style={{ marginTop: 12, fontSize: '11px' }}>
        Adjust {scenario.hazard_type.replaceAll('_', ' ')} parameters above, then run simulation.
        Outcomes are deterministic prototype projections, not validated forecasts.
      </p>
    </div>
  )
}
