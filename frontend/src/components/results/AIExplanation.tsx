import { useSimulation } from '../../context/SimulationContext'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { ErrorBanner } from '../common/ErrorBanner'

export function AIExplanation() {
  const {
    simulationResult,
    explanation,
    explanationLoading,
    fetchExplanation,
    error,
  } = useSimulation()

  if (!simulationResult) return null

  const isFallback = explanation?.fallback === true

  return (
    <div className="ops-explanation">
      {error && <ErrorBanner message={error} />}

      {!explanation && !explanationLoading && (
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <p className="muted" style={{ fontSize: '13px', marginBottom: 14 }}>
            Get a plain-language explanation of why the simulation recommends
            <strong> {simulationResult.recommended_strategy.replace(/_/g, ' ')}</strong>.
            The recommendation itself comes from the deterministic engine.
          </p>
          <button
            type="button"
            onClick={fetchExplanation}
            disabled={explanationLoading}
            className="ops-run-button"
          >
            Explain recommendation
          </button>
        </div>
      )}

      {explanationLoading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
          <LoadingSpinner label="Building explanation from simulation results..." />
        </div>
      )}

      {explanation && (
        <div style={{ display: 'grid', gap: 12 }}>
          <div className={`ops-explanation-callout${isFallback ? ' is-fallback' : ''}`}>
            {isFallback
              ? 'Deterministic fallback explanation — grounded in simulation results. No language model was used for this response.'
              : 'Explanation grounded in deterministic simulation results. The engine selected the recommendation; this text only explains it.'}
          </div>
          <div className="ops-explanation-body">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span className="ops-explanation-title">
                {isFallback ? 'Deterministic fallback' : 'Simulation explanation'}
              </span>
              <span className="muted" style={{ fontSize: '11px' }}>
                · {explanation.strategy_explained.replace(/_/g, ' ')}
              </span>
            </div>
            <div style={{ whiteSpace: 'pre-line' }}>{explanation.explanation}</div>
          </div>
          <button
            type="button"
            onClick={fetchExplanation}
            disabled={explanationLoading}
            className="ops-secondary-button"
            style={{ width: 'fit-content' }}
          >
            Refresh explanation
          </button>
        </div>
      )}
    </div>
  )
}
