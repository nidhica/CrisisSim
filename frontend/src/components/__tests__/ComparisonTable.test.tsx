import { render, screen, within } from '@testing-library/react'
import { ComparisonTable } from '../results/ComparisonTable'
import type { InterventionResult } from '../../types'

function makeIntervention(strategy: string, label: string, rec = 0.5): InterventionResult {
  return {
    strategy: strategy as InterventionResult['strategy'], label,
    zone_results: [],
    avg_risk_score: 50, avg_response_time_minutes: 30,
    risk_reduction_pct: rec, response_time_improvement_minutes: 5,
    bottleneck_resolution_score: 0.3, resource_cost: 2, composite_score: 0.6,
  }
}

describe('ComparisonTable', () => {
  const interventions = [
    makeIntervention('baseline', 'Baseline / No Intervention', 0),
    makeIntervention('resource_reallocation', 'Resource Reallocation', 10),
    makeIntervention('capacity_expansion', 'Capacity Expansion', 5),
    makeIntervention('combined', 'Combined Intervention', 20),
  ]

  it('renders all four strategies', () => {
    render(<ComparisonTable interventions={interventions} recommendedStrategy="combined" />)
    const table = screen.getByRole('table')
    expect(within(table).getByText('Baseline / No Intervention')).toBeInTheDocument()
    expect(within(table).getByText('Combined Intervention')).toBeInTheDocument()
  })

  it('shows Recommended badge on recommended strategy', () => {
    render(<ComparisonTable interventions={interventions} recommendedStrategy="combined" />)
    expect(screen.getByText('Recommended')).toBeInTheDocument()
  })
})
