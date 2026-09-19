import { render, screen, fireEvent } from '@testing-library/react'
import { BeforeAfterToggle } from '../results/BeforeAfterToggle'
import type { SimulationResult, ZoneResult } from '../../types'

function makeZoneResult(zone_id: string, risk_score: number): ZoneResult {
  return {
    zone_id, risk_score, risk_level: 'high', response_time_minutes: 30,
    risk_components: {
      affected_population_score: 0, flood_severity_score: 0,
      medical_urgency_score: 0, road_accessibility_score: 0, resource_shortage_score: 0,
    },
  }
}

const mockResult: SimulationResult = {
  result_id: 'r1', scenario_id: 's1', run_at: '2026-01-01T00:00:00Z',
  params_used: [],
  baseline_zone_results: [makeZoneResult('zone-1', 70), makeZoneResult('zone-2', 40)],
  bottlenecks: [],
  interventions: [{
    strategy: 'combined', label: 'Combined Intervention',
    zone_results: [makeZoneResult('zone-1', 55), makeZoneResult('zone-2', 30)],
    avg_risk_score: 42.5, avg_response_time_minutes: 25,
    risk_reduction_pct: 21, response_time_improvement_minutes: 10,
    bottleneck_resolution_score: 0.5, resource_cost: 3, composite_score: 0.8,
  }],
  recommended_strategy: 'combined',
}

describe('BeforeAfterToggle', () => {
  it('shows Before view by default', () => {
    render(<BeforeAfterToggle result={mockResult} />)
    expect(screen.getByText(/baseline/i)).toBeInTheDocument()
  })
  it('switches to After view', () => {
    render(<BeforeAfterToggle result={mockResult} />)
    fireEvent.click(screen.getByText(/after/i))
    expect(screen.getByText(/risk reduction/i)).toBeInTheDocument()
  })
})
