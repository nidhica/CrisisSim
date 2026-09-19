import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Incident, Scenario } from '../../types'
import {
  ScenarioFromIncidentError,
  buildEmergencyConfigurationFromIncident,
  createScenarioFromIncident,
  findHazardScenarioSummary,
} from '../createScenarioFromIncident'
import { mapIncidentSeverityToScenario } from '../../constants/hazardScenarioDefaults'

const baseIncident: Incident = {
  incident_id: 'INC-2026-0042',
  hazard_type: 'fire',
  location_name: 'Bhopal, Madhya Pradesh, India',
  latitude: 23.2599,
  longitude: 77.4126,
  severity: 'high',
  description: 'Heavy smoke near the market.',
  status: 'acknowledged',
  created_at: '2026-01-01T00:00:00.000Z',
}

const sourceScenario: Scenario = {
  scenario_id: 'fire-scenario-001',
  name: 'Fire template',
  description: 'Template',
  severity: 'high',
  created_at: '2026-01-01',
  hazard_type: 'fire',
  population_max: 5000,
  zones: [
    {
      zone_id: 'zone-1',
      name: 'Z1',
      coordinates: [[51.5, -0.1]],
      centroid: [51.5, -0.1],
      flood_severity: 0.2,
      affected_population: 100,
      medical_urgency: 0.5,
      road_accessibility: 0.5,
      rescue_teams: 2,
      ambulances: 1,
      demand_units: 10,
      hazard_factors: {},
      specialist_resources: {},
    },
    {
      zone_id: 'zone-2',
      name: 'Z2',
      coordinates: [[51.51, -0.11]],
      centroid: [51.51, -0.11],
      flood_severity: 0.2,
      affected_population: 100,
      medical_urgency: 0.5,
      road_accessibility: 0.5,
      rescue_teams: 2,
      ambulances: 1,
      demand_units: 10,
      hazard_factors: {},
      specialist_resources: {},
    },
  ],
  shelters: [
    {
      shelter_id: 's1',
      name: 'Shelter',
      coordinates: [51.5, -0.1],
      capacity: 100,
      current_occupancy: 10,
    },
  ],
  hospitals: [
    {
      hospital_id: 'h1',
      name: 'Hospital',
      coordinates: [51.5, -0.1],
      capacity: 50,
      surge_capacity: 10,
      current_occupancy: 5,
    },
  ],
}

describe('createScenarioFromIncident', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000)
  })

  it('maps moderate severity to medium for scenarios', () => {
    expect(mapIncidentSeverityToScenario('moderate')).toBe('medium')
    expect(mapIncidentSeverityToScenario('critical')).toBe('critical')
  })

  it('finds matching hazard template', () => {
    const summary = findHazardScenarioSummary(
      [
        { scenario_id: 'flood-scenario-001', name: 'F', description: '', severity: 'high', hazard_type: 'flood' },
        { scenario_id: 'fire-scenario-001', name: 'Fire', description: '', severity: 'high', hazard_type: 'fire' },
      ],
      'fire',
    )
    expect(summary?.scenario_id).toBe('fire-scenario-001')
  })

  it('passes incident location and hazard into demo scenario config', () => {
    const config = buildEmergencyConfigurationFromIncident(baseIncident)
    expect(config.hazardType).toBe('fire')
    expect(config.location?.latitude).toBeCloseTo(23.2599)
    expect(config.location?.displayName).toContain('Bhopal')
    expect(config.sourceIncidentId).toBe('INC-2026-0042')
    expect(config.severity).toBe('high')
  })

  it('creates demo scenario with source_incident_id and Bhopal coordinates', () => {
    const demo = createScenarioFromIncident(baseIncident, sourceScenario)
    expect(demo.sourceScenarioId).toBe('fire-scenario-001')
    expect(demo.scenario.source_incident_id).toBe('INC-2026-0042')
    expect(demo.scenario.hazard_type).toBe('fire')
    expect(demo.scenario.latitude).toBeCloseTo(23.2599)
    expect(demo.scenario.longitude).toBeCloseTo(77.4126)
    expect(demo.scenario.name).toContain('Bhopal')
    expect(demo.scenario.name).toContain('INC-2026-0042')
    expect(demo.scenario.zones[0].hazard_factors?.fire_intensity).toBeDefined()
    expect(demo.scenario.zones[0].specialist_resources?.fire_crews).toBe(2)
  })

  it('rejects missing location', () => {
    expect(() =>
      buildEmergencyConfigurationFromIncident({
        ...baseIncident,
        latitude: Number.NaN,
      }),
    ).toThrow(ScenarioFromIncidentError)
  })

  it('returns undefined when hazard template is missing', () => {
    expect(
      findHazardScenarioSummary(
        [{ scenario_id: 'flood-scenario-001', name: 'F', description: '', severity: 'high', hazard_type: 'flood' }],
        'fire',
      ),
    ).toBeUndefined()
  })
})
