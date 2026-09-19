import { render, screen } from '@testing-library/react'
import { ProjectedImpact } from '../ProjectedImpact'
import type { InterventionResult } from '../../../types'

const baseline: InterventionResult = {
  strategy: 'baseline',
  label: 'Baseline',
  zone_results: [],
  avg_risk_score: 43.2,
  avg_response_time_minutes: 44.2,
  risk_reduction_pct: 0,
  response_time_improvement_minutes: 0,
  bottleneck_resolution_score: 0.2,
  resource_cost: 0,
  composite_score: 0.5,
}

const recommended: InterventionResult = {
  strategy: 'resource_reallocation',
  label: 'Resource Reallocation',
  zone_results: [],
  avg_risk_score: 39.8,
  avg_response_time_minutes: 40.1,
  risk_reduction_pct: 7.9,
  response_time_improvement_minutes: 4.1,
  bottleneck_resolution_score: 0.55,
  resource_cost: 2,
  composite_score: 0.7,
}

describe('ProjectedImpact', () => {
  it('shows baseline vs recommended deltas', () => {
    render(<ProjectedImpact baseline={baseline} recommended={recommended} />)
    const panel = screen.getByRole('region', { name: /projected impact/i })
    expect(panel).toHaveTextContent('43.2 → 39.8')
    expect(panel).toHaveTextContent('39.8')
    expect(panel).toHaveTextContent(/projected impact/i)
    expect(panel).toHaveTextContent(/simulation only/i)
  })

  it('renders nothing when strategies match', () => {
    const { container } = render(<ProjectedImpact baseline={baseline} recommended={baseline} />)
    expect(container).toBeEmptyDOMElement()
  })
})
