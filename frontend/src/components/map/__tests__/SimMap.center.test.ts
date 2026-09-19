import { describe, expect, it } from 'vitest'
import type { Scenario } from '../../../types'

/** Mirror resolveMapCenter logic from SimMap for unit testing without Leaflet DOM. */
function resolveMapCenter(scenario: Scenario): [number, number] {
  if (scenario.latitude != null && scenario.longitude != null) {
    return [scenario.latitude, scenario.longitude]
  }
  if (scenario.zones.length > 0) {
    return [scenario.zones[0].centroid[0], scenario.zones[0].centroid[1]]
  }
  return [51.505, -0.09]
}

describe('SimMap center resolution', () => {
  it('uses scenario latitude/longitude when present', () => {
    const center = resolveMapCenter({
      scenario_id: 'x',
      name: 'Test',
      description: '',
      severity: 'high',
      created_at: '',
      zones: [{ zone_id: 'zone-1', name: 'Z1', coordinates: [], centroid: [51.5, -0.09], flood_severity: 0.5, affected_population: 1, medical_urgency: 0.5, road_accessibility: 0.5, rescue_teams: 1, ambulances: 1, demand_units: 1 }],
      shelters: [],
      hospitals: [],
      population_max: 1000,
      hazard_type: 'fire',
      latitude: 23.25,
      longitude: 77.41,
    })
    expect(center).toEqual([23.25, 77.41])
  })

  it('falls back to first zone centroid without location fields', () => {
    const center = resolveMapCenter({
      scenario_id: 'x',
      name: 'Test',
      description: '',
      severity: 'high',
      created_at: '',
      zones: [{ zone_id: 'zone-1', name: 'Z1', coordinates: [], centroid: [51.5125, -0.085], flood_severity: 0.5, affected_population: 1, medical_urgency: 0.5, road_accessibility: 0.5, rescue_teams: 1, ambulances: 1, demand_units: 1 }],
      shelters: [],
      hospitals: [],
      population_max: 1000,
      hazard_type: 'flood',
    })
    expect(center).toEqual([51.5125, -0.085])
  })
})
