import { describe, expect, it } from 'vitest'
import type { HazardType, Scenario, Zone } from '../../types'
import { createDemoScenario } from '../demoScenarios'
import {
  generateLocationScenarioGeometry,
  isNearLondon,
  locationShortName,
  repositionSimulatedFacilities,
} from '../generateLocationScenarioGeometry'

const BHOPAL = { latitude: 23.2599, longitude: 77.4126 }

function makeTemplateZone(id: string): Zone {
  return {
    zone_id: id,
    name: `Zone ${id}`,
    coordinates: [[51.51, -0.09], [51.51, -0.08], [51.50, -0.08], [51.50, -0.09]],
    centroid: [51.505, -0.085],
    flood_severity: 0.5,
    affected_population: 1000,
    medical_urgency: 0.5,
    road_accessibility: 0.5,
    rescue_teams: 2,
    ambulances: 2,
    demand_units: 5,
    hazard_factors: {},
    specialist_resources: {},
  }
}

function makeSourceScenario(hazardType: HazardType = 'fire'): Scenario {
  const zones = ['zone-1', 'zone-2', 'zone-3', 'zone-4', 'zone-5'].map(makeTemplateZone)
  return {
    scenario_id: `${hazardType}-scenario-001`,
    name: 'Template',
    description: 'Template scenario',
    severity: 'high',
    created_at: '2026-01-01T00:00:00Z',
    zones,
    shelters: [
      {
        shelter_id: 'shelter-1',
        name: 'Community Centre',
        coordinates: [51.512, -0.087],
        capacity: 500,
        current_occupancy: 420,
      },
    ],
    hospitals: [
      {
        hospital_id: 'hospital-1',
        name: 'General Hospital',
        coordinates: [51.516, -0.082],
        capacity: 200,
        surge_capacity: 50,
        current_occupancy: 180,
      },
    ],
    population_max: 15000,
    hazard_type: hazardType,
  }
}

describe('generateLocationScenarioGeometry', () => {
  it('generates five zones centered around selected coordinates', () => {
    const zones = generateLocationScenarioGeometry(
      BHOPAL.latitude,
      BHOPAL.longitude,
      'fire',
      makeSourceScenario().zones,
    )

    expect(zones).toHaveLength(5)
    expect(zones.map(z => z.zone_id)).toEqual([
      'zone-1',
      'zone-2',
      'zone-3',
      'zone-4',
      'zone-5',
    ])

    for (const zone of zones) {
      expect(zone.name).toMatch(/^Simulated Zone \d/)
      expect(isNearLondon(zone.centroid[0], zone.centroid[1])).toBe(false)
      const distLat = Math.abs(zone.centroid[0] - BHOPAL.latitude)
      const distLng = Math.abs(zone.centroid[1] - BHOPAL.longitude)
      expect(distLat).toBeLessThan(0.02)
      expect(distLng).toBeLessThan(0.02)
    }
  })

  it('repositions facilities away from London', () => {
    const source = makeSourceScenario()
    const { shelters, hospitals } = repositionSimulatedFacilities(
      BHOPAL.latitude,
      BHOPAL.longitude,
      source.shelters,
      source.hospitals,
    )

    expect(shelters[0].shelter_id).toBe('shelter-1')
    expect(hospitals[0].hospital_id).toBe('hospital-1')
    expect(shelters[0].name).toMatch(/^Simulated /)
    expect(isNearLondon(shelters[0].coordinates[0], shelters[0].coordinates[1])).toBe(false)
    expect(isNearLondon(hospitals[0].coordinates[0], hospitals[0].coordinates[1])).toBe(false)
  })

  it('locationShortName extracts city segment', () => {
    expect(locationShortName('Bhopal, Madhya Pradesh, India')).toBe('Bhopal')
  })
})

describe('createDemoScenario location integration', () => {
  const hazards: HazardType[] = [
    'flood',
    'fire',
    'earthquake',
    'cyclone',
    'industrial_accident',
  ]

  it('stores location and regenerates geometry when location provided', () => {
    const source = makeSourceScenario('fire')
    const demo = createDemoScenario(source, {
      name: 'Bhopal Fire Emergency',
      severity: 'high',
      affectedZones: 3,
      populationAffected: 1200,
      floodSeverity: 0.75,
      medicalUrgency: 0.6,
      roadAccessibility: 0.45,
      rescueTeams: 4,
      ambulances: 2,
      hazardType: 'fire',
      hazardFactors: {
        fire_intensity: 0.8,
        smoke_exposure: 0.65,
        spread_potential: 0.7,
      },
      specialistResources: { fire_crews: 2 },
      location: {
        displayName: 'Bhopal, Madhya Pradesh, India',
        latitude: BHOPAL.latitude,
        longitude: BHOPAL.longitude,
      },
      hazardLabel: 'Fire',
    })

    expect(demo.scenario.location_name).toBe('Bhopal, Madhya Pradesh, India')
    expect(demo.scenario.latitude).toBe(BHOPAL.latitude)
    expect(demo.scenario.longitude).toBe(BHOPAL.longitude)
    expect(demo.scenario.description).toContain('Location-aware simulated')
    expect(demo.scenario.zones[0].hazard_factors?.fire_intensity).toBe(0.8)
    expect(demo.scenario.zones[0].specialist_resources?.fire_crews).toBe(2)
    expect(isNearLondon(demo.scenario.zones[0].centroid[0], demo.scenario.zones[0].centroid[1])).toBe(
      false,
    )
  })

  it('preserves London geometry when no location is provided', () => {
    const source = makeSourceScenario('flood')
    const demo = createDemoScenario(source, {
      name: 'London Flood',
      severity: 'high',
      affectedZones: 2,
      populationAffected: 1200,
      floodSeverity: 0.75,
      medicalUrgency: 0.6,
      roadAccessibility: 0.45,
      rescueTeams: 4,
      ambulances: 2,
      hazardType: 'flood',
      hazardFactors: { flood_severity: 0.75 },
      specialistResources: {},
    })

    expect(demo.scenario.latitude).toBeUndefined()
    expect(demo.scenario.longitude).toBeUndefined()
    expect(isNearLondon(demo.scenario.zones[0].centroid[0], demo.scenario.zones[0].centroid[1])).toBe(
      true,
    )
  })

  it.each(hazards)('preserves hazard-specific params for %s', hazardType => {
    const source = makeSourceScenario(hazardType)
    const hazardFactors: Record<string, number> =
      hazardType === 'flood'
        ? { flood_severity: 0.7 }
        : hazardType === 'fire'
          ? { fire_intensity: 0.8, smoke_exposure: 0.6, spread_potential: 0.7 }
          : hazardType === 'earthquake'
            ? {
                structural_damage: 0.8,
                trapped_person_likelihood: 0.6,
                aftershock_risk: 0.4,
              }
            : hazardType === 'cyclone'
              ? {
                  wind_severity: 0.8,
                  storm_surge_exposure: 0.6,
                  power_outage_severity: 0.7,
                }
              : {
                  toxic_release_severity: 0.8,
                  exposure_level: 0.6,
                  containment_failure: 0.7,
                }

    const specialistResources: Record<string, number> =
      hazardType === 'fire'
        ? { fire_crews: 2 }
        : hazardType === 'earthquake'
          ? { search_and_rescue_teams: 2 }
          : hazardType === 'cyclone'
            ? { evacuation_teams: 2, utility_crews: 1 }
            : hazardType === 'industrial_accident'
              ? { hazmat_teams: 2, containment_units: 1 }
              : {}

    const demo = createDemoScenario(source, {
      name: `${hazardType} test`,
      severity: 'high',
      affectedZones: 2,
      populationAffected: 1000,
      floodSeverity: 0.7,
      medicalUrgency: 0.5,
      roadAccessibility: 0.5,
      rescueTeams: 3,
      ambulances: 2,
      hazardType,
      hazardFactors,
      specialistResources,
      location: {
        displayName: 'Bengaluru, Karnataka, India',
        latitude: 12.9716,
        longitude: 77.5946,
      },
    })

    expect(demo.scenario.hazard_type).toBe(hazardType)
    expect(demo.scenario.zones[0].hazard_factors).toEqual(hazardFactors)
    if (hazardType !== 'flood') {
      expect(demo.scenario.zones[0].specialist_resources).toEqual(specialistResources)
    }
  })
})
