import { render, screen } from '@testing-library/react'
import { CommandBrief } from '../CommandBrief'
import type { Scenario, SimulationResult } from '../../../types'

const scenario: Scenario = {
  scenario_id: 'fire-scenario-001',
  name: 'Bhopal Fire Emergency',
  description: 'Demo',
  severity: 'high',
  created_at: '2026-01-01',
  hazard_type: 'fire',
  population_max: 1000,
  location_name: 'Bhopal, Madhya Pradesh, India',
  source_incident_id: 'INC-2026-0001',
  zones: [
    {
      zone_id: 'zone-1',
      name: 'Zone 1',
      coordinates: [[23.25, 77.41]],
      centroid: [23.25, 77.41],
      flood_severity: 0.2,
      affected_population: 100,
      medical_urgency: 0.5,
      road_accessibility: 0.5,
      rescue_teams: 2,
      ambulances: 1,
      demand_units: 10,
    },
  ],
  shelters: [],
  hospitals: [],
}

const result: SimulationResult = {
  result_id: 'r1',
  scenario_id: 'fire-scenario-001',
  run_at: '2026-01-01',
  params_used: [],
  baseline_zone_results: [
    {
      zone_id: 'zone-1',
      risk_score: 43.2,
      risk_level: 'high',
      response_time_minutes: 44.2,
      risk_components: {
        affected_population_score: 1,
        flood_severity_score: 1,
        medical_urgency_score: 1,
        road_accessibility_score: 1,
        resource_shortage_score: 1,
      },
    },
  ],
  bottlenecks: [
    {
      type: 'fire_crew_shortage',
      zone_id: 'zone-1',
      facility_id: null,
      description: 'Fire crew shortage in Zone 1',
      severity_score: 0.8,
    },
  ],
  interventions: [
    {
      strategy: 'baseline',
      label: 'Baseline / No Intervention',
      zone_results: [],
      avg_risk_score: 43.2,
      avg_response_time_minutes: 44.2,
      risk_reduction_pct: 0,
      response_time_improvement_minutes: 0,
      bottleneck_resolution_score: 0.2,
      resource_cost: 0,
      composite_score: 0.5,
    },
    {
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
    },
  ],
  recommended_strategy: 'resource_reallocation',
  hazard_type: 'fire',
}

describe('CommandBrief', () => {
  it('renders empty state without results', () => {
    render(<CommandBrief scenario={scenario} result={null} isRunning={false} />)
    expect(screen.getByText(/response command brief/i)).toBeInTheDocument()
    expect(screen.getByText(/run a deterministic simulation/i)).toBeInTheDocument()
  })

  it('renders metrics from existing simulation data', () => {
    render(<CommandBrief scenario={scenario} result={result} isRunning={false} />)
    const brief = screen.getByRole('region', { name: /response command brief/i })
    expect(brief).toHaveTextContent('Resource Reallocation')
    expect(brief).toHaveTextContent('43.2')
    expect(brief).toHaveTextContent('Highest-risk zone')
    expect(brief).toHaveTextContent('Fire crew shortage in Zone 1')
    expect(brief).toHaveTextContent('Primary bottleneck')
  })
})
